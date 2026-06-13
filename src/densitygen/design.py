"""Inverse design: *propose* novel precursors, don't just screen a given list.

The generative loop combinatorially assembles a metal center with ligand
fragments from a curated library (homoleptic M(L)_n plus a few heteroleptic
mixes and common motifs like carbonyls), then scores every proposal with the
exact same scorecard the screener uses. UMA -- when enabled -- is the cheap
evaluation that makes searching this space affordable: each proposal is a few
seconds, not an hour of DFT.

This is the "model proposes molecules you didn't list" capability. A nice
sanity check falls out for free: for tungsten the loop re-derives WF6/WCl6 (the
known-good recipes) near the top, which validates that the search is sane.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from densitygen.chem import ATOMIC_WEIGHT, Composition, parse_formula
from densitygen.data import KNOWN_PRECURSORS, lookup_precursor
from densitygen.schemas import CandidateResult, ModelProvenance, ScreeningResponse
from densitygen.screen import (
    billing_from_backend,
    build_scorecard,
    compute_uma_signals,
    resolve_film,
    _simulation_calls,
)
from densitygen.compute import get_backend


@dataclass(frozen=True)
class Ligand:
    label: str               # how it shows in a formula, e.g. "NMe2"
    atoms: dict              # per-ligand element counts (excluding the bond to metal)
    ligand_class: str
    anionic: bool = True     # consumes one unit of metal oxidation state


# Curated monodentate ligand library spanning the chemistries ALD precursors
# actually use: halides, alkyls, alkylamides, alkoxides, hydride, and neutral CO.
LIGANDS: dict[str, Ligand] = {
    "F": Ligand("F", {"F": 1}, "halide"),
    "Cl": Ligand("Cl", {"Cl": 1}, "halide"),
    "Me": Ligand("CH3", {"C": 1, "H": 3}, "alkyl"),
    "Et": Ligand("C2H5", {"C": 2, "H": 5}, "alkyl"),
    "NMe2": Ligand("N(CH3)2", {"N": 1, "C": 2, "H": 6}, "alkylamide"),
    "NEtMe": Ligand("N(C2H5)(CH3)", {"N": 1, "C": 3, "H": 8}, "alkylamide"),
    "OtBu": Ligand("OC4H9", {"O": 1, "C": 4, "H": 9}, "alkoxide"),
    "OEt": Ligand("OC2H5", {"O": 1, "C": 2, "H": 5}, "alkoxide"),
    "H": Ligand("H", {"H": 1}, "hydride"),
    "CO": Ligand("CO", {"C": 1, "O": 1}, "carbonyl", anionic=False),
}

# Representative oxidation state used to set ligand count for each film metal.
METAL_OXIDATION = {"W": 6, "Mo": 6, "Ti": 4, "Hf": 4, "Zr": 4, "Al": 3,
                   "Ta": 5, "Ru": 3, "La": 3, "V": 5, "Nb": 5, "Sn": 4,
                   "Co": 3, "Ir": 3, "Rh": 3, "Ni": 2, "Cu": 2}


def _composition(metal: str, parts: list[tuple[str, int]]) -> tuple[Composition, str]:
    """Build a Composition and a display formula from metal + [(ligand_key, n)]."""
    counts: dict[str, float] = {metal: 1.0}
    formula_bits = [metal]
    for key, n in parts:
        if n == 0:
            continue
        lig = LIGANDS[key]
        for el, c in lig.atoms.items():
            counts[el] = counts.get(el, 0.0) + c * n
        formula_bits.append(f"({lig.label}){n}" if n > 1 else f"({lig.label})")
    comp = Composition(counts={k: v for k, v in counts.items() if v}, formula_input="".join(formula_bits))
    return comp, comp.formula_input


def generate(metal: str, oxidation: int, ligand_keys: list[str] | None = None,
             allow_mixed: bool = True) -> list[tuple[str, Composition, str]]:
    """Enumerate proposed precursors for `metal`. Returns (name, comp, ligand_class)."""
    keys = ligand_keys or list(LIGANDS.keys())
    out: list[tuple[str, Composition, str]] = []
    seen: set[str] = set()

    def emit(parts, lclass):
        comp, formula = _composition(metal, parts)
        sig = tuple(sorted((el, n) for el, n in comp.counts.items()))
        if sig in seen:
            return
        seen.add(sig)
        out.append((formula, comp, lclass))

    # Homoleptic anionic: M(L)_oxidation
    for k in keys:
        lig = LIGANDS[k]
        if lig.anionic:
            emit([(k, oxidation)], lig.ligand_class)

    # Neutral carbonyl motif: M(CO)_oxidation (group-6 carbonyls etc.)
    if "CO" in keys:
        emit([("CO", oxidation)], "carbonyl")

    # Heteroleptic mixes of two anionic ligands summing to the oxidation state.
    if allow_mixed:
        anionic = [k for k in keys if LIGANDS[k].anionic]
        for a, b in itertools.combinations(anionic, 2):
            for na in (oxidation - 1, oxidation // 2, 2):
                nb = oxidation - na
                if 1 <= na < oxidation and nb >= 1:
                    emit([(a, na), (b, nb)], "mixed")
    return out


def _identify_known(comp: Composition):
    """If a proposed composition matches a known precursor, return it (so the
    loop can flag 'rediscovered a real recipe')."""
    target = {el: n for el, n in comp.counts.items()}
    for kp in KNOWN_PRECURSORS.values():
        try:
            kc = parse_formula(kp.formula)
        except Exception:
            continue
        if {e: n for e, n in kc.counts.items()} == target:
            return kp
    return None


def design(*, film: str, co_reactant: str | None = None, temperature_max_c: float | None = None,
           forbidden_elements: list[str] | None = None, oxidation: int | None = None,
           top_n: int = 12, ligand_keys: list[str] | None = None,
           use_ml_potential: bool = False, uma_top_k: int = 3) -> ScreeningResponse:
    """Propose and rank novel precursors for a target film.

    UMA is applied only to the top `uma_top_k` descriptor-ranked survivors --
    the escalation ladder in action: cheap descriptors triage the whole
    combinatorial set, real physics confirms only the finalists.
    """
    film_obj, warnings = resolve_film(film)
    forbidden_elements = forbidden_elements or []
    metal = film_obj.film_element
    ox = oxidation or METAL_OXIDATION.get(metal, 4)
    if metal not in ATOMIC_WEIGHT:
        warnings.append(f"Unknown metal '{metal}'; cannot generate precursors.")
        return ScreeningResponse(film=film, co_reactant=co_reactant, ranked_candidates=[],
                                 warnings=warnings,
                                 model_provenance=ModelProvenance(compute_backend="local-descriptors"))

    proposals = generate(metal, ox, ligand_keys)

    # First pass: descriptor-only scorecards for everything.
    results: list[CandidateResult] = []
    for formula, comp, lclass in proposals:
        known = _identify_known(comp)
        name = known.name if known else formula
        card = build_scorecard(
            name=name, comp=comp, known=known, film=film_obj,
            co_reactant=co_reactant, temperature_max_c=temperature_max_c,
            forbidden_elements=forbidden_elements, origin="proposed",
            is_known=bool(known))
        results.append(card)

    results.sort(key=lambda r: r.overall_score, reverse=True)
    results = results[:top_n]

    # Second pass: escalate the top survivors to real UMA energies.
    used_uma = False
    backend = get_backend() if use_ml_potential else None
    if use_ml_potential and backend is None:
        warnings.append("use_ml_potential set but no UMA backend reachable; descriptors only.")
    if backend is not None:
        for card in results[:uma_top_k]:
            try:
                comp = parse_formula(card.formula)
                call_start = len(getattr(backend, "calls", []))
                ml_e, ads, notes, ml_backend = compute_uma_signals(
                    card.name, comp, film_obj, backend)
                ml_calls = _simulation_calls(backend, call_start)
                warnings.extend(notes)
                if ml_e is None and ads is None:
                    continue
                used_uma = True
                known = lookup_precursor(card.name)
                rescored = build_scorecard(
                    name=card.name, comp=comp, known=known, film=film_obj,
                    co_reactant=co_reactant, temperature_max_c=temperature_max_c,
                    forbidden_elements=forbidden_elements, ads_energy=ads,
                    ml_energy_ev=ml_e, used_uma=True, ml_backend=ml_backend,
                    ml_calls=ml_calls, origin="proposed",
                    is_known=card.is_known_recipe)
                results[results.index(card)] = rescored
            except Exception as e:
                warnings.append(f"{card.name}: UMA escalation failed ({e}).")
        results.sort(key=lambda r: r.overall_score, reverse=True)

    backend_label = {
        "LocalUMA": "uma-local",
        "LocalMACE": "mace-local",
        "LocalCHGNet": "chgnet-local",
        "MLPotentialClient": "uma-replicate",
    }.get(type(backend).__name__, "ml-potential") if used_uma else "local-descriptors"
    prov = ModelProvenance(
        compute_backend=backend_label,
        model_name=getattr(backend, "model", None) if used_uma else None,
        notes=(f"Generated {len(proposals)} candidates; descriptor-triaged to "
               f"{len(results)}" + (f", ML-confirmed top {uma_top_k}." if used_uma else ".")))
    return ScreeningResponse(film=film, co_reactant=co_reactant, ranked_candidates=results,
                             warnings=warnings, model_provenance=prov,
                             billing=billing_from_backend(backend))
