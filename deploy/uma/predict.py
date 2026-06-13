"""Replicate Cog predictor: Meta FAIR UMA (uma-s-1p2) energies/forces.

This is the hosted compute backend the DensityGen screener calls when
`use_ml_potential=true`. It takes an atomic structure (extxyz) plus a UMA task
head and returns the potential energy and forces -- the atomistic physics that
would otherwise require a DFT run on a supercomputer.

Task heads:
    omol -> molecular energetics (precursor stability, ligand-bond strength)
    oc20 -> adsorption energy on a slab (surface chemisorption / self-limiting)
    omat -> bulk/surface formation energies (is the film thermodynamically OK)
"""

from __future__ import annotations

import os
from io import StringIO

from cog import BasePredictor, Input


class Predictor(BasePredictor):
    def setup(self) -> None:
        # REASON: UMA weights on HuggingFace are gated. HF_TOKEN must be set as a
        # Replicate *secret* env var and the weights downloaded here at cold
        # start -- NOT at build time. The Cog build environment has no secrets,
        # and baking gated weights into the image would violate the HF license.
        # Cold-start download is ~1-2 GB and is then cached in the container.
        from fairchem.core import pretrained_mlip, FAIRChemCalculator

        if not os.environ.get("HF_TOKEN"):
            raise RuntimeError(
                "HF_TOKEN secret not set; UMA weights are gated on HuggingFace."
            )
        self._FAIRChemCalculator = FAIRChemCalculator
        self._predictor = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")

    def predict(
        self,
        xyz: str = Input(description="Atomic structure in extxyz format"),
        task: str = Input(
            description="UMA task head", default="omol",
            choices=["omol", "oc20", "omat"],
        ),
        relax: bool = Input(
            description="Relax the geometry (LBFGS) before reporting energy",
            default=True,
        ),
        fmax: float = Input(description="Force convergence (eV/A) for relaxation", default=0.05),
        steps: int = Input(description="Max relaxation steps", default=100),
    ) -> dict:
        from ase.io import read
        from ase.optimize import LBFGS

        atoms = read(StringIO(xyz), format="extxyz")
        atoms.calc = self._FAIRChemCalculator(self._predictor, task_name=task)
        if relax:
            LBFGS(atoms, logfile=None).run(fmax=fmax, steps=steps)
        return {
            "energy": float(atoms.get_potential_energy()),
            "forces": atoms.get_forces().tolist(),
            "task": task,
            "n_atoms": len(atoms),
        }
