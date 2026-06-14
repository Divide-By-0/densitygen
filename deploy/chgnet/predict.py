"""Replicate Cog predictor: CHGNet energies/forces — the ungated real ML
interatomic potential the DensityGen screener calls for hosted real-simulation.

Same wire contract as the UMA predictor (deploy/uma): in = {xyz, task, relax},
out = {energy, forces}. So `DENSITYGEN_UMA_MODEL` can point at either model and
the screener's MLPotentialClient works unchanged.

CHGNet is a *materials* potential trained on Materials Project crystals, so it
is trustworthy for slabs/bulk and a labeled proxy for isolated precursor
molecules. It needs a periodic cell, so bare molecules are wrapped in a vacuum
box before evaluation.
"""

from __future__ import annotations

from io import StringIO

from cog import BasePredictor, Input


class Predictor(BasePredictor):
    def setup(self) -> None:
        # Weights ship inside the chgnet package -> no network, no gated access.
        from chgnet.model import CHGNetCalculator
        self.calc = CHGNetCalculator(use_device="cpu")

    def predict(
        self,
        xyz: str = Input(description="Atomic structure in extxyz format"),
        task: str = Input(description="Task label (interface parity with UMA)",
                          default="omat", choices=["omol", "oc20", "omat"]),
        relax: bool = Input(description="Relax geometry (LBFGS) before energy", default=True),
        fmax: float = Input(description="Force convergence (eV/A)", default=0.05),
        steps: int = Input(description="Max relaxation steps", default=60),
    ) -> dict:
        from ase.io import read
        from ase.optimize import LBFGS

        atoms = read(StringIO(xyz), format="extxyz")
        # CHGNet requires a periodic cell; wrap bare molecules in a vacuum box.
        if not atoms.cell.rank:
            atoms.center(vacuum=6.0)
            atoms.pbc = True
        atoms.calc = self.calc
        if relax:
            LBFGS(atoms, logfile=None).run(fmax=fmax, steps=steps)
        return {
            "energy": float(atoms.get_potential_energy()),
            "forces": atoms.get_forces().tolist(),
            "task": task,
            "n_atoms": len(atoms),
        }
