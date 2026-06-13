"""ASE structure bridge: turn a precursor identity into 3D atoms that UMA can
evaluate, and build slab + adsorbate systems for adsorption energies.

Key design point: UMA relaxes geometries (LBFGS) before reporting an energy, so
we do NOT need accurate starting coordinates -- only a sensible, non-overlapping
guess. That lets us build metal-halide precursors (WF6, TiCl4, MoF6, ...) from
pure coordination geometry without RDKit. Polyatomic-ligand organometallics
(TMA, TEMAH) that we can't yet place return None, and the screener transparently
falls back to descriptors for those.

All ASE imports are local so the rest of the package keeps working without ASE.
"""

from __future__ import annotations

import math
from typing import Optional

from densitygen.chem import HALOGENS, Composition

# Approximate metal-ligand bond lengths (Angstrom). Coarse on purpose --
# relaxation moves them to the true minimum; these only need to avoid overlap.
_BOND = {"F": 1.83, "Cl": 2.27, "Br": 2.45, "I": 2.70, "O": 1.95, "N": 1.95,
         "C": 2.10, "H": 1.70}

# Unit-vector vertex sets for each coordination number -> molecular geometry.
_GEOMETRY = {
    1: [(0, 0, 1)],
    2: [(0, 0, 1), (0, 0, -1)],
    3: [(1, 0, 0), (-0.5, 0.8660, 0), (-0.5, -0.8660, 0)],            # trigonal planar
    4: [(0.5774, 0.5774, 0.5774), (0.5774, -0.5774, -0.5774),         # tetrahedral
        (-0.5774, 0.5774, -0.5774), (-0.5774, -0.5774, 0.5774)],
    5: [(0, 0, 1), (0, 0, -1), (1, 0, 0),                             # trigonal bipyramidal
        (-0.5, 0.8660, 0), (-0.5, -0.8660, 0)],
    6: [(1, 0, 0), (-1, 0, 0), (0, 1, 0),                             # octahedral
        (0, -1, 0), (0, 0, 1), (0, 0, -1)],
}


def is_simple_metal_halide(comp: Composition) -> Optional[tuple[str, str, int]]:
    """If the composition is a single metal + single halogen species (MX_n),
    return (metal, halogen, n). Else None."""
    metals = [el for el in comp.counts if el not in HALOGENS and el != "H"]
    halos = list(comp.halogens.keys())
    if len(metals) == 1 and len(halos) == 1 and comp.count("H") == 0 \
            and comp.count("C") == 0 and comp.count("O") == 0 and comp.count("N") == 0:
        n = int(comp.count(halos[0]))
        if n in _GEOMETRY:
            return metals[0], halos[0], n
    return None


def build_molecule(name: str, comp: Composition):
    """Return an ase.Atoms for a precursor, or None if we can't place it.

    Strategy: (1) try ASE's built-in molecule database by name (covers H2O,
    NH3, CO, CH4, ...); (2) build metal halides from coordination geometry;
    (3) give up (None) for polyatomic-ligand organometallics.
    """
    try:
        from ase import Atoms
        from ase.build import molecule as ase_molecule
    except Exception:
        return None

    # (1) Known small molecules straight from ASE's G2 set.
    try:
        return ase_molecule(name)
    except Exception:
        pass

    # (2) Metal halide MX_n from a coordination polyhedron.
    mh = is_simple_metal_halide(comp)
    if mh is not None:
        metal, halo, n = mh
        d = _BOND.get(halo, 2.0)
        symbols = [metal]
        positions = [(0.0, 0.0, 0.0)]
        for vx, vy, vz in _GEOMETRY[n]:
            norm = math.sqrt(vx * vx + vy * vy + vz * vz) or 1.0
            positions.append((vx / norm * d, vy / norm * d, vz / norm * d))
            symbols.append(halo)
        return Atoms(symbols=symbols, positions=positions)

    return None


# Crystal structure of the elemental metals we build slabs for, so we pick the
# right ASE surface constructor.
_LATTICE = {"W": "bcc", "Mo": "bcc", "Ta": "bcc", "Al": "fcc", "Cu": "fcc",
            "Ni": "fcc", "Ru": "hcp", "Ti": "hcp", "Pt": "fcc", "Ir": "fcc"}
_A0 = {"W": 3.16, "Mo": 3.15, "Ta": 3.30, "Al": 4.05, "Cu": 3.61, "Ni": 3.52,
       "Pt": 3.92, "Ir": 3.84}


def build_metal_slab(element: str, size=(3, 3, 3), vacuum: float = 8.0):
    """Build a relaxable metal slab for the film element, or None if unknown."""
    try:
        from ase.build import bcc110, fcc111, hcp0001
    except Exception:
        return None
    lat = _LATTICE.get(element)
    if lat == "bcc":
        return bcc110(element, size=size, vacuum=vacuum, a=_A0.get(element))
    if lat == "fcc":
        return fcc111(element, size=size, vacuum=vacuum, a=_A0.get(element))
    if lat == "hcp":
        return hcp0001(element, size=size, vacuum=vacuum)
    return None


def build_adsorption_system(slab, molecule, height: float = 2.2):
    """Place `molecule` above the slab. Returns a new combined Atoms."""
    from ase.build import add_adsorbate
    sys = slab.copy()
    # REASON: add_adsorbate attaches by an atom index; index 0 is the metal
    # center for our halides, so the metal points at the surface (the reactive
    # atom), which is the chemically meaningful adsorption geometry.
    add_adsorbate(sys, molecule.copy(), height=height, position=(
        slab.cell[0][0] / 2, slab.cell[1][1] / 2), mol_index=0)
    return sys


def to_extxyz(atoms) -> str:
    """Serialize ase.Atoms to an extxyz string (the wire format for the
    Replicate UMA backend)."""
    from io import StringIO
    from ase.io import write
    buf = StringIO()
    write(buf, atoms, format="extxyz")
    return buf.getvalue()
