"""Lightweight cheminformatics with no hard third-party dependency.

RDKit is great but heavy and frequently absent (it is not installed in many
GPU/serving images). Everything the screener strictly needs -- molecular
weight, element inventory, heteroatom/carbon content, halogen flags -- can be
derived from a molecular formula, which we can parse in pure Python. RDKit, if
present, is used only to upgrade a SMILES string into a formula; we never make
it a hard requirement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# REASON: Curated atomic weights (g/mol) for the elements that actually appear
# in ALD precursors, co-reactants, and films. Kept small and explicit instead
# of pulling in a periodic-table dependency. Add elements here as needed.
ATOMIC_WEIGHT: dict[str, float] = {
    "H": 1.008, "B": 10.811, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "Na": 22.990, "Mg": 24.305, "Al": 26.982, "Si": 28.085,
    "P": 30.974, "S": 32.06, "Cl": 35.45, "K": 39.098, "Ca": 40.078,
    "Ti": 47.867, "V": 50.942, "Cr": 51.996, "Mn": 54.938, "Fe": 55.845,
    "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38, "Ga": 69.723,
    "Ge": 72.63, "As": 74.922, "Se": 78.971, "Br": 79.904, "Y": 88.906,
    "Zr": 91.224, "Nb": 92.906, "Mo": 95.95, "Ru": 101.07, "Rh": 102.906,
    "Pd": 106.42, "Ag": 107.868, "In": 114.818, "Sn": 118.71, "Sb": 121.76,
    "Te": 127.6, "I": 126.904, "La": 138.905, "Hf": 178.49, "Ta": 180.948,
    "W": 183.84, "Re": 186.207, "Os": 190.23, "Ir": 192.217, "Pt": 195.084,
    "Au": 196.967, "Pb": 207.2, "Bi": 208.980,
}

# Elements that constitute the deposited *film* metal/semimetal of interest.
# Used to decide which atom in a precursor is the "payload".
FILM_FORMING_ELEMENTS = {
    "Al", "Ti", "Hf", "Zr", "W", "Ta", "Ru", "Mo", "Si", "Ga", "In", "Sn",
    "Zn", "La", "Y", "V", "Nb", "Co", "Ni", "Cu", "Pt", "Ir", "Pd", "Ge",
    "Re", "Os", "Rh", "Ag", "Au", "Mn", "Cr", "Fe",
}

HALOGENS = {"F", "Cl", "Br", "I"}

_TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\[|\]|\d+)")


@dataclass
class Composition:
    """Parsed elemental composition of a molecule."""

    counts: dict[str, float] = field(default_factory=dict)
    formula_input: str = ""

    @property
    def molecular_weight(self) -> float:
        return round(sum(ATOMIC_WEIGHT.get(el, 0.0) * n for el, n in self.counts.items()), 3)

    @property
    def n_atoms(self) -> int:
        return int(sum(self.counts.values()))

    @property
    def n_heavy_atoms(self) -> int:
        return int(sum(n for el, n in self.counts.items() if el != "H"))

    def count(self, element: str) -> float:
        return self.counts.get(element, 0.0)

    @property
    def carbon_fraction(self) -> float:
        """Carbon atoms / heavy atoms -- a crude carbon-contamination proxy."""
        if self.n_heavy_atoms == 0:
            return 0.0
        return self.count("C") / self.n_heavy_atoms

    @property
    def halogens(self) -> dict[str, float]:
        return {el: n for el, n in self.counts.items() if el in HALOGENS and n}

    def film_element(self, prefer: str | None = None) -> str | None:
        """Best guess at the payload (film-forming) element in this molecule."""
        present = [el for el in self.counts if el in FILM_FORMING_ELEMENTS]
        if prefer and prefer in present:
            return prefer
        if not present:
            return None
        # REASON: When several film-forming elements are present (e.g. an
        # organosilicon Hf precursor) pick the heaviest -- in practice the
        # intended payload metal is the heaviest such atom (Hf over Si).
        return max(present, key=lambda el: ATOMIC_WEIGHT.get(el, 0.0))


class FormulaError(ValueError):
    pass


def parse_formula(formula: str) -> Composition:
    """Parse a molecular formula with nested ()/[] groups, e.g. ``Al(CH3)3`` or
    ``Hf[N(CH3)2]4``. Returns elemental counts.

    This is deliberately a *formula* parser, not a SMILES parser. SMILES is
    converted to a formula upstream (via RDKit if available) before reaching
    here.
    """
    formula = formula.strip().replace(" ", "")
    if not formula:
        raise FormulaError("empty formula")

    tokens = _TOKEN.findall(formula)
    # Reconstruct to detect garbage the tokenizer silently dropped.
    if "".join(tokens) != formula:
        raise FormulaError(f"could not fully parse formula: {formula!r}")

    stack: list[dict[str, float]] = [{}]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("(", "["):
            stack.append({})
        elif tok in (")", "]"):
            group = stack.pop()
            mult = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                mult = int(tokens[i + 1])
                i += 1
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0.0) + n * mult
        elif tok.isdigit():
            # A bare number right after an element is handled in the element
            # branch; a stray leading number is invalid.
            raise FormulaError(f"unexpected count {tok!r} in {formula!r}")
        else:  # element symbol
            if tok not in ATOMIC_WEIGHT:
                raise FormulaError(f"unknown element {tok!r} in {formula!r}")
            count = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                count = int(tokens[i + 1])
                i += 1
            stack[-1][tok] = stack[-1].get(tok, 0.0) + count
        i += 1

    if len(stack) != 1:
        raise FormulaError(f"unbalanced brackets in {formula!r}")

    comp = Composition(counts={k: v for k, v in stack[0].items() if v}, formula_input=formula)
    if comp.n_atoms == 0:
        raise FormulaError(f"no atoms parsed from {formula!r}")
    return comp


def smiles_to_formula(smiles: str) -> str | None:
    """Convert SMILES -> Hill-notation formula using RDKit if available.

    Returns ``None`` when RDKit is not installed or the SMILES is invalid, so
    callers can fall back to asking the user for an explicit formula.
    """
    try:
        from rdkit import Chem  # type: ignore
        from rdkit.Chem import rdMolDescriptors  # type: ignore
    except Exception:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return rdMolDescriptors.CalcMolFormula(mol)


def to_composition(*, formula: str | None = None, smiles: str | None = None) -> Composition:
    """Resolve a Composition from whichever identifier the caller supplied."""
    if formula:
        return parse_formula(formula)
    if smiles:
        f = smiles_to_formula(smiles)
        if f is None:
            raise FormulaError(
                f"could not parse SMILES {smiles!r} (RDKit unavailable or invalid); "
                "supply an explicit molecular formula instead"
            )
        return parse_formula(f)
    raise FormulaError("need a formula or SMILES to build a composition")
