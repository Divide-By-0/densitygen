"""ML-potential compute layer.

This is the seam between the ALD scoring logic and the actual atomistic
physics. The screener calls into here for energies; *how* those energies are
produced (a hosted UMA model on Replicate, a local fairchem install, or
nothing) is hidden behind one interface so the rest of the system never
changes.

Design decision (see README): no MLIP is pre-hosted on Replicate, so the real
backend is **Meta FAIR's UMA (`uma-s-1p2`) deployed by us as a Cog model**.
Until that model is pushed, `use_ml_potential=False` keeps the whole tool
working on the local descriptor scorer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


# Task heads of the UMA model. Picked per calculation:
#   omol -> molecular energetics (precursor stability, ligand bonds)
#   oc20 -> adsorption energy of a molecule on a slab (surface reactivity)
#   omat -> bulk/surface formation energies (is the film favorable?)
UMA_TASKS = ("omol", "oc20", "omat")

DEFAULT_REPLICATE_MODEL = os.environ.get(
    # REASON: Overridable so whoever deploys the Cog model can point the client
    # at their own Replicate slug without code changes. Format: "owner/name" or
    # "owner/name:version".
    "DENSITYGEN_UMA_MODEL",
    "densitygen/uma-ald",
)


@dataclass
class EnergyResult:
    energy_ev: float
    backend: str
    task: str
    forces: Optional[list] = None
    note: str = ""


class ComputeUnavailable(RuntimeError):
    """Raised when a real ML-potential energy was requested but no backend is
    reachable. Callers should catch this and fall back to descriptors."""


class MLPotentialClient:
    """Calls the hosted UMA model on Replicate to get energies/forces.

    The client is intentionally thin: it ships an (ext)xyz structure plus a
    task head and returns energy/forces. Structure *generation* (3D coords,
    slab building, adsorbate placement) lives upstream, because that is where
    ASE/RDKit are needed and where the chemistry decisions are made.
    """

    def __init__(self, model: str | None = None, token: str | None = None):
        self.model = model or DEFAULT_REPLICATE_MODEL
        self.token = token or os.environ.get("REPLICATE_API_TOKEN")

    @property
    def available(self) -> bool:
        if not self.token:
            return False
        try:
            import replicate  # noqa: F401
        except Exception:
            return False
        return True

    def energy(self, xyz: str, task: str = "omol", *, relax: bool = True) -> EnergyResult:
        """Single energy (optionally relaxed) for a structure given as extxyz."""
        if task not in UMA_TASKS:
            raise ValueError(f"task must be one of {UMA_TASKS}, got {task!r}")
        if not self.available:
            raise ComputeUnavailable(
                "UMA-on-Replicate backend unreachable: set REPLICATE_API_TOKEN "
                "and `pip install replicate`, and deploy the Cog model "
                f"({self.model})."
            )
        import replicate

        client = replicate.Client(api_token=self.token)
        out = client.run(
            self.model,
            input={"xyz": xyz, "task": task, "relax": relax},
        )
        # Cog predictor returns {"energy": float, "forces": [[...]]}.
        if not isinstance(out, dict) or "energy" not in out:
            raise ComputeUnavailable(f"unexpected UMA response shape: {type(out)}")
        return EnergyResult(
            energy_ev=float(out["energy"]),
            backend="uma-replicate",
            task=task,
            forces=out.get("forces"),
            note=f"UMA {task} via {self.model}",
        )

    def adsorption_energy(
        self, *, system_xyz: str, slab_xyz: str, molecule_xyz: str
    ) -> EnergyResult:
        """E_ads = E(slab+adsorbate) - E(slab) - E(gas molecule).

        Negative => exothermic chemisorption (good for self-limiting ALD).
        Slab/system use the oc20 head; the gas molecule uses omol.
        """
        e_sys = self.energy(system_xyz, task="oc20").energy_ev
        e_slab = self.energy(slab_xyz, task="oc20").energy_ev
        e_mol = self.energy(molecule_xyz, task="omol").energy_ev
        e_ads = e_sys - e_slab - e_mol
        return EnergyResult(
            energy_ev=e_ads,
            backend="uma-replicate",
            task="oc20",
            note="adsorption energy (eV); negative = favorable chemisorption",
        )


class LocalUMA:
    """Run UMA in-process via fairchem-core (no network). This is what makes the
    tool actually compute real atomistic energies on this machine.

    Loading the predictor is expensive, so it is cached on first use. Device
    defaults to CPU for reliability (some fairchem ops are unimplemented on MPS);
    override with DENSITYGEN_UMA_DEVICE=mps|cuda|cpu.
    """

    _predictor = None  # class-level cache: load the model once per process

    def __init__(self, model: str = "uma-s-1p2", device: str | None = None):
        self.model = model
        self.device = device or os.environ.get("DENSITYGEN_UMA_DEVICE", "cpu")

    @property
    def available(self) -> bool:
        try:
            import fairchem  # noqa: F401
        except Exception:
            return False
        return bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"))

    def _predict_unit(self):
        if LocalUMA._predictor is None:
            from fairchem.core import pretrained_mlip
            LocalUMA._predictor = pretrained_mlip.get_predict_unit(self.model, device=self.device)
        return LocalUMA._predictor

    def energy_atoms(self, atoms, task: str = "omol", *, relax: bool = True,
                     fmax: float = 0.05, steps: int = 100) -> EnergyResult:
        """Relaxed potential energy (eV) of an ase.Atoms for a UMA task head."""
        if task not in UMA_TASKS:
            raise ValueError(f"task must be one of {UMA_TASKS}, got {task!r}")
        if not self.available:
            raise ComputeUnavailable(
                "Local UMA unavailable: need `pip install fairchem-core` and an "
                "HF_TOKEN with access to the gated facebook/UMA weights."
            )
        from fairchem.core import FAIRChemCalculator
        from ase.optimize import LBFGS

        work = atoms.copy()
        work.calc = FAIRChemCalculator(self._predict_unit(), task_name=task)
        if relax:
            LBFGS(work, logfile=None).run(fmax=fmax, steps=steps)
        return EnergyResult(
            energy_ev=float(work.get_potential_energy()),
            backend="uma-local",
            task=task,
            note=f"UMA {task} (local, device={self.device})",
        )

    def adsorption_energy_atoms(self, *, system, slab, molecule) -> EnergyResult:
        e_sys = self.energy_atoms(system, task="oc20").energy_ev
        e_slab = self.energy_atoms(slab, task="oc20").energy_ev
        e_mol = self.energy_atoms(molecule, task="omol").energy_ev
        return EnergyResult(
            energy_ev=e_sys - e_slab - e_mol,
            backend="uma-local",
            task="oc20",
            note="adsorption energy (eV); negative = favorable chemisorption",
        )


class LocalMACE:
    """Ungated universal MLIP fallback (MACE-MP-0) via mace-torch.

    UMA is the preferred engine, but its weights are gated on HuggingFace and
    approval can lag. MACE-MP-0 is a genuine universal foundation potential with
    *ungated* weights, so it lets the tool compute real atomistic energies today
    on the same ase.Atoms interface. It does not have UMA's molecule-specific
    head, so it is a stand-in for demonstrating the physics path, not a claim of
    UMA-equivalent accuracy on organics.
    """

    _calc = None  # cache the calculator (model download) once per process

    def __init__(self, model: str = "small", device: str | None = None):
        self.model = f"mace-mp-0-{model}"
        self.device = device or os.environ.get("DENSITYGEN_UMA_DEVICE", "cpu")
        self._size = model

    @property
    def available(self) -> bool:
        try:
            import mace  # noqa: F401
        except Exception:
            return False
        return True

    def _calculator(self):
        if LocalMACE._calc is None:
            from mace.calculators import mace_mp
            LocalMACE._calc = mace_mp(model=self._size, device=self.device,
                                      default_dtype="float64")
        return LocalMACE._calc

    def energy_atoms(self, atoms, task: str = "omol", *, relax: bool = True,
                     fmax: float = 0.05, steps: int = 60) -> EnergyResult:
        # task is accepted for interface parity with UMA; MACE has one head.
        if not self.available:
            raise ComputeUnavailable("mace-torch not installed")
        from ase.optimize import LBFGS

        work = atoms.copy()
        work.calc = self._calculator()
        if relax:
            LBFGS(work, logfile=None).run(fmax=fmax, steps=steps)
        return EnergyResult(
            energy_ev=float(work.get_potential_energy()),
            backend="mace-local",
            task=task,
            note=f"MACE-MP-0 ({self._size}) energy, device={self.device}",
        )

    def adsorption_energy_atoms(self, *, system, slab, molecule) -> EnergyResult:
        e_sys = self.energy_atoms(system, relax=True).energy_ev
        e_slab = self.energy_atoms(slab, relax=True).energy_ev
        e_mol = self.energy_atoms(molecule, relax=True).energy_ev
        return EnergyResult(
            energy_ev=e_sys - e_slab - e_mol,
            backend="mace-local",
            task="oc20",
            note="adsorption energy (eV) via MACE-MP-0; negative = favorable",
        )


class LocalCHGNet:
    """Working, ungated real-MLIP backend (CHGNet) — the one that actually runs
    in this environment today.

    CHGNet ships its weights inside the pip package (no gated download, no
    network), so it computes real energies/forces offline. It is a *materials*
    potential (trained on Materials Project inorganic crystals), so it is most
    trustworthy for slabs and bulk formation energies; for isolated precursor
    molecules it is out-of-domain and the number is a relative proxy, not a
    UMA-omol-grade value. We surface it as real-but-proxy, never overclaim.
    """

    _calc = None

    def __init__(self, device: str | None = None):
        self.model = "chgnet-0.3.0"
        self.device = device or os.environ.get("DENSITYGEN_UMA_DEVICE", "cpu")

    @property
    def available(self) -> bool:
        try:
            import chgnet  # noqa: F401
        except Exception:
            return False
        return True

    def _calculator(self):
        if LocalCHGNet._calc is None:
            from chgnet.model import CHGNetCalculator
            LocalCHGNet._calc = CHGNetCalculator(use_device=self.device)
        return LocalCHGNet._calc

    @staticmethod
    def _periodic(atoms):
        # REASON: CHGNet requires a periodic cell. Molecules built by structures.py
        # have none, so wrap them in a vacuum box; slabs already carry a cell.
        work = atoms.copy()
        if not work.cell.rank:
            work.center(vacuum=6.0)
            work.pbc = True
        return work

    def energy_atoms(self, atoms, task: str = "omat", *, relax: bool = True,
                     fmax: float = 0.05, steps: int = 60) -> EnergyResult:
        if not self.available:
            raise ComputeUnavailable("chgnet not installed")
        from ase.optimize import LBFGS

        work = self._periodic(atoms)
        work.calc = self._calculator()
        if relax:
            LBFGS(work, logfile=None).run(fmax=fmax, steps=steps)
        return EnergyResult(
            energy_ev=float(work.get_potential_energy()),
            backend="chgnet-local",
            task=task,
            note=f"CHGNet energy (real, ungated), device={self.device}",
        )

    def adsorption_energy_atoms(self, *, system, slab, molecule) -> EnergyResult:
        e_sys = self.energy_atoms(system).energy_ev
        e_slab = self.energy_atoms(slab).energy_ev
        e_mol = self.energy_atoms(molecule).energy_ev
        return EnergyResult(
            energy_ev=e_sys - e_slab - e_mol,
            backend="chgnet-local",
            task="oc20",
            note="adsorption energy (eV) via CHGNet; negative = favorable",
        )


def get_backend(prefer_local: bool = True, allow_mace: bool = True):
    """Pick the best reachable atomistic backend, or None.

    Preference: local UMA (gated, best) -> hosted UMA on Replicate -> local
    MACE-MP-0 (ungated, always-works fallback) -> None (descriptor scoring).
    """
    if prefer_local:
        uma = LocalUMA()
        if uma.available:
            try:
                uma._predict_unit()  # force the gated download to fail fast here
                return uma
            except Exception:
                pass  # gated/unavailable -> fall through to remote / MACE
    remote = MLPotentialClient()
    if remote.available:
        # NOTE: only trust remote if a model slug other than the default
        # placeholder is configured; otherwise it would 404 at call time.
        if os.environ.get("DENSITYGEN_UMA_MODEL"):
            return remote
    if allow_mace:
        mace = LocalMACE()
        if mace.available:
            try:
                mace._calculator()  # fail fast if mace's deps are broken
                return mace
            except Exception:
                pass
    chg = LocalCHGNet()
    if chg.available:
        return chg
    return None
