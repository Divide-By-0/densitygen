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


# Light (ligand) elements; anything else in a precursor is the metal center.
_LIGHT = {"H", "C", "N", "O", "F", "Cl", "Br", "I"}

# Homoleptic ligand fragments we can place: per-ligand element counts + the atom
# that bonds the metal (carbonyls bond through C, amides through N, alkoxides
# through O, alkyls through C). Matched against M(L)_k stoichiometry.
_LIGAND_SIG: dict[str, tuple[dict, str]] = {
    "CO":    ({"C": 1, "O": 1}, "C"),            # carbonyl  -> W(CO)6, Mo(CO)6, Ni(CO)4
    "CH3":   ({"C": 1, "H": 3}, "C"),            # methyl    -> TMA Al(CH3)3
    "C2H5":  ({"C": 2, "H": 5}, "C"),            # ethyl
    "C5H5":  ({"C": 5, "H": 5}, "C"),            # cyclopentadienyl
    "NMe2":  ({"N": 1, "C": 2, "H": 6}, "N"),    # dimethylamide -> TDMAH/TDMAT
    "NEtMe": ({"N": 1, "C": 3, "H": 8}, "N"),    # ethylmethylamide -> TEMAH
    "OEt":   ({"O": 1, "C": 2, "H": 5}, "O"),    # ethoxide
    "OtBu":  ({"O": 1, "C": 4, "H": 9}, "O"),    # tert-butoxide -> Hf(OtBu)4
    "H":     ({"H": 1}, "H"),                    # hydride
}


def _decompose_homoleptic(comp: Composition):
    """If `comp` is one metal + k identical ligands (M(L)_k) we can place,
    return (metal, k, ligand_key, coord_element). Else None."""
    counts = {e: int(round(n)) for e, n in comp.counts.items() if n}
    metals = [e for e in counts if e not in _LIGHT]
    if len(metals) != 1 or counts[metals[0]] != 1:
        return None
    metal = metals[0]
    rem = {e: counts[e] for e in counts if e != metal}
    if not rem:
        return None
    for key, (sig, coord) in _LIGAND_SIG.items():
        if set(rem) != set(sig):
            continue
        k = None
        for e, per in sig.items():
            if rem[e] % per:
                k = None
                break
            kk = rem[e] // per
            k = kk if k is None else (k if k == kk else -1)
        if k and k > 0 and k in _GEOMETRY:
            return metal, k, key, coord
    return None


def _frame(u):
    """An orthonormal pair perpendicular to unit vector u."""
    ax = (0.0, 0.0, 1.0) if abs(u[2]) < 0.9 else (1.0, 0.0, 0.0)
    e1 = (u[1] * ax[2] - u[2] * ax[1], u[2] * ax[0] - u[0] * ax[2], u[0] * ax[1] - u[1] * ax[0])
    n = math.sqrt(sum(c * c for c in e1)) or 1.0
    e1 = tuple(c / n for c in e1)
    e2 = (u[1] * e1[2] - u[2] * e1[1], u[2] * e1[0] - u[0] * e1[2], u[0] * e1[1] - u[1] * e1[0])
    return e1, e2


def _place_ligand(coord_sym, others, P, u):
    """Place one ligand: coordinating atom at P, the rest fanned outward along u.

    Coordinates are deliberately coarse but non-overlapping -- UMA/CHGNet relax
    (LBFGS) before reporting an energy, so a sane connected guess is enough.
    """
    e1, e2 = _frame(u)
    atoms = [(coord_sym, P)]
    heavies = [s for s in others if s != "H"]
    hs = [s for s in others if s == "H"]
    # Linear special-case: a lone heavy partner (CO) sits straight out (M-C-O).
    if heavies == ["O"] and coord_sym == "C" and not hs:
        atoms.append(("O", tuple(P[i] + u[i] * 1.15 for i in range(3))))
        return atoms
    centers = []
    base = tuple(P[i] + u[i] * 1.5 for i in range(3))
    for i, s in enumerate(heavies):
        ang = 2 * math.pi * i / max(1, len(heavies))
        off = [(e1[j] * math.cos(ang) + e2[j] * math.sin(ang)) * 0.75 + u[j] * 0.35 * i for j in range(3)]
        pos = tuple(base[j] + off[j] for j in range(3))
        atoms.append((s, pos)); centers.append(pos)
    if not centers:
        centers = [tuple(P[i] + u[i] * 1.0 for i in range(3))]
    for j, s in enumerate(hs):
        c = centers[j % len(centers)]
        ang = 2 * math.pi * j / max(1, len(hs)) + 0.6
        off = [(e1[k] * math.cos(ang) + e2[k] * math.sin(ang)) * 0.95 + u[k] * 0.45 for k in range(3)]
        atoms.append((s, tuple(c[k] + off[k] for k in range(3))))
    return atoms


def build_molecule(name: str, comp: Composition):
    """Return an ase.Atoms for a precursor, or None if we can't place it.

    Strategy: (1) ASE's built-in molecule database by name (H2O, NH3, CO, CH4,
    ...); (2) metal halides MX_n from a coordination polyhedron; (3) homoleptic
    organometallics M(L)_k (carbonyls, alkyls, amides, alkoxides); (4) give up.
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

    # (3) Homoleptic organometallic M(L)_k -- carbonyls, alkyls, amides, alkoxides.
    homo = _decompose_homoleptic(comp)
    if homo is not None:
        metal, k, key, coord = homo
        d = _BOND.get(coord, 2.05)
        symbols = [metal]
        positions = [(0.0, 0.0, 0.0)]
        sig = _LIGAND_SIG[key][0]
        # the ligand's atoms minus its coordinating atom, as a flat element list
        others = []
        for el, cnt in sig.items():
            others += [el] * (cnt - (1 if el == coord else 0))
        for vx, vy, vz in _GEOMETRY[k]:
            norm = math.sqrt(vx * vx + vy * vy + vz * vz) or 1.0
            u = (vx / norm, vy / norm, vz / norm)
            P = (u[0] * d, u[1] * d, u[2] * d)
            for sym, pos in _place_ligand(coord, others, P, u):
                symbols.append(sym); positions.append(pos)
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
