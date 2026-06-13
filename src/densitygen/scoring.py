"""ALD viability scoring.

Turns molecular descriptors, curated literature data, and (optionally) real
UMA energies into an interpretable scorecard. Every component carries its own
evidence string and a confidence tag (measured / estimated / unknown) so a
chemist can see *why* a candidate moved up or down -- the tool triages, it does
not pretend to be an oracle.

The hard gates matter most: a precursor that does not contain the film's
payload element cannot deposit that film, no matter how volatile it is. Those
are enforced before the soft scores are even averaged.
"""

from __future__ import annotations

from typing import Optional

from densitygen.chem import Composition
from densitygen.compute import EnergyResult
from densitygen.data import CO_REACTANTS, Film, KnownPrecursor
from densitygen.schemas import ScoreComponent

# Weights for combining the seven soft components into an overall score.
# Delivery + thermal window dominate because a precursor that won't volatilize
# or that decomposes in the line is dead on arrival regardless of chemistry.
WEIGHTS = {
    "delivery": 0.20,
    "thermal_window": 0.18,
    "surface_reactivity": 0.17,
    "self_limiting": 0.13,
    "clean_ligand": 0.14,
    "byproduct": 0.10,
    "integration": 0.08,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _ramp(x: float, lo: float, hi: float) -> float:
    """Linear 0->1 as x goes lo->hi (clamped). Used for smooth descriptor maps."""
    if hi == lo:
        return 1.0 if x >= hi else 0.0
    return _clamp((x - lo) / (hi - lo))


# ---------------------------------------------------------------------------
# Individual score components
# ---------------------------------------------------------------------------

def score_delivery(comp: Composition, known: Optional[KnownPrecursor]) -> ScoreComponent:
    """Volatility / deliverability as vapor."""
    if known and known.bubbler_temp_c is not None:
        # Lower required source temperature == more volatile == easier delivery.
        s = _ramp(200.0 - known.bubbler_temp_c, 0.0, 180.0)
        ev = f"Source/bubbler ~{known.bubbler_temp_c:.0f} C ({known.vapor_pressure_note})"
        return ScoreComponent(name="delivery", score=round(_clamp(s), 3), evidence=ev, confidence="measured")

    # REASON: With no measured vapor pressure, molecular weight is the most
    # reliable cheap proxy for volatility -- lighter metal-organics sublime/boil
    # more readily. Halides skew volatile; very heavy/oligomeric species do not.
    mw = comp.molecular_weight
    s = _ramp(700.0 - mw, 0.0, 550.0)
    if comp.halogens and not comp.count("C"):
        s = _clamp(s + 0.1)  # simple metal halides tend to be volatile
    ev = f"MW={mw:.1f} g/mol (volatility estimated from molecular weight)"
    return ScoreComponent(name="delivery", score=round(_clamp(s), 3), evidence=ev, confidence="estimated")


def score_thermal_window(
    comp: Composition, known: Optional[KnownPrecursor], temp_max_c: Optional[float], ligand_class: str
) -> ScoreComponent:
    """Does it survive to the wafer and have a self-limiting window at the cap?"""
    if known and known.decomposition_onset_c is not None:
        onset = known.decomposition_onset_c
        if temp_max_c is None:
            s = _ramp(onset, 150.0, 450.0)
            ev = f"Decomposition onset ~{onset:.0f} C (no process cap given)"
        elif temp_max_c >= onset:
            # Process runs above self-decomposition -> CVD-like, not self-limiting.
            s = _clamp(0.3 - (temp_max_c - onset) / 300.0)
            ev = f"Process cap {temp_max_c:.0f} C exceeds decomposition onset {onset:.0f} C"
        else:
            margin = onset - temp_max_c
            s = _clamp(0.5 + _ramp(margin, 0.0, 150.0) * 0.5)
            ev = f"Decomposition onset {onset:.0f} C is {margin:.0f} C above process cap"
        return ScoreComponent(name="thermal_window", score=round(s, 3), evidence=ev, confidence="measured")

    # Estimate stability ordering from ligand chemistry.
    base = {"halide": 0.85, "hydride": 0.5, "alkylamide": 0.55, "alkyl": 0.5,
            "alkoxide": 0.6, "cyclopentadienyl": 0.65, "betadiketonate": 0.7}.get(ligand_class, 0.55)
    ev = f"Thermal stability estimated from ligand class '{ligand_class or 'unknown'}'"
    return ScoreComponent(name="thermal_window", score=round(base, 3), evidence=ev, confidence="estimated")


def score_clean_ligand(comp: Composition, ligand_class: str) -> ScoreComponent:
    """Residue risk -- carbon contamination and halide incorporation."""
    cfrac = comp.carbon_fraction
    carbon_penalty = cfrac * 0.6  # heavy carbon ligands leave C in the film
    halo_penalty = 0.0
    notes = []
    if comp.count("F"):
        halo_penalty += 0.25  # F is hard to fully remove; HF chemistry
        notes.append("fluorine residue/HF risk")
    if comp.count("Cl"):
        halo_penalty += 0.15
        notes.append("chlorine residue")
    if cfrac > 0:
        notes.append(f"carbon fraction {cfrac:.0%}")
    s = _clamp(1.0 - carbon_penalty - halo_penalty)
    ev = "Clean elimination likely" if not notes else "Residue watch: " + ", ".join(notes)
    return ScoreComponent(name="clean_ligand", score=round(s, 3), evidence=ev, confidence="estimated")


def score_surface_reactivity(
    film: Film, co_reactant: Optional[str], ligand_class: str, ads_energy: Optional[EnergyResult]
) -> ScoreComponent:
    """Will it chemisorb / exchange on the target surface?"""
    if ads_energy is not None:
        # Map adsorption energy (eV) to a score: more negative == more favorable.
        # ~ -1.5 eV or stronger is solid chemisorption; ~0 is physisorption only.
        e = ads_energy.energy_ev
        s = _ramp(-e, 0.0, 2.0)
        # REASON: only a UMA-grade backend earns "measured". A proxy materials
        # potential (CHGNet/MACE) on an out-of-domain precursor molecule gives a
        # real number but not a trustworthy one, so it stays "estimated".
        is_uma = ads_energy.backend.startswith("uma")
        ev = f"adsorption energy {e:+.2f} eV ({ads_energy.note})"
        return ScoreComponent(name="surface_reactivity", score=round(s, 3),
                              evidence=ev, confidence="measured" if is_uma else "estimated")

    # Heuristic: reactive ligands exchange with surface -OH / -NHx / metal sites.
    reactive = {"halide": 0.8, "alkyl": 0.85, "alkylamide": 0.8, "hydride": 0.7,
                "alkoxide": 0.65, "cyclopentadienyl": 0.6, "betadiketonate": 0.55}.get(ligand_class, 0.6)
    # Co-reactant aggressiveness helps drive the exchange half-reaction.
    cr = CO_REACTANTS.get(co_reactant or "")
    boost = 0.1 * (cr.aggressiveness if cr else 0.4)
    s = _clamp(reactive * 0.85 + boost)
    ev = f"Ligand-exchange reactivity estimated for '{ligand_class}' ligands"
    if cr:
        ev += f" with {cr.name} ({cr.role})"
    return ScoreComponent(name="surface_reactivity", score=round(s, 3), evidence=ev, confidence="estimated")


def score_self_limiting(comp: Composition, ligand_class: str) -> ScoreComponent:
    """Steric saturation -> growth stops after one layer."""
    # Bulkier ligand shells saturate the surface and shut off further adsorption.
    bulk = {"alkylamide": 0.85, "cyclopentadienyl": 0.8, "betadiketonate": 0.8,
            "alkoxide": 0.7, "alkyl": 0.7, "halide": 0.6, "hydride": 0.45}.get(ligand_class, 0.6)
    # Larger molecules (more atoms per metal) are more sterically self-limiting.
    metal = comp.film_element()
    per_metal = comp.n_heavy_atoms / max(1.0, comp.count(metal) if metal else 1.0)
    bulk = _clamp(bulk + _ramp(per_metal, 1.0, 8.0) * 0.1)
    ev = f"Steric self-limiting estimated from '{ligand_class}' ligand bulk"
    return ScoreComponent(name="self_limiting", score=round(bulk, 3), evidence=ev, confidence="estimated")


def score_byproduct(comp: Composition, co_reactant: Optional[str], ligand_class: str) -> ScoreComponent:
    """Are the reaction byproducts benign, or do they etch/corrode?"""
    s = 0.9
    notes = []
    if comp.count("F"):
        s -= 0.45  # HF etches oxides/Si -- the WF6 integration headache
        notes.append("HF byproduct etches oxides/Si")
    elif comp.count("Cl"):
        s -= 0.25
        notes.append("HCl byproduct, mildly corrosive")
    if ligand_class in ("alkyl", "alkylamide", "alkoxide") and comp.count("F") == 0:
        notes.append("hydrocarbon/amine byproducts, benign")
    s = _clamp(s)
    ev = "Benign byproducts" if not notes else "; ".join(notes)
    return ScoreComponent(name="byproduct", score=round(s, 3), evidence=ev, confidence="estimated")


# ---------------------------------------------------------------------------
# Hard gates + aggregation
# ---------------------------------------------------------------------------

def evaluate_gates(
    comp: Composition, film: Film, forbidden: list[str]
) -> tuple[float, list[str]]:
    """Return an integration score and any disqualifying warnings.

    A precursor that cannot deliver the film element is a hard fail (overall
    score is forced to 0 downstream). A forbidden element is not an automatic
    zero but is heavily penalized -- the integration component collapses to
    0.1, which sinks the candidate's rank while still letting a chemist see the
    rest of its scorecard and decide.
    """
    warnings: list[str] = []
    score = 0.9

    if comp.count(film.film_element) <= 0:
        warnings.append(
            f"HARD FAIL: candidate contains no {film.film_element}; it cannot "
            f"deposit {film.formula}."
        )
        score = 0.0

    for el in forbidden:
        if comp.count(el) > 0:
            warnings.append(f"Contains forbidden element {el}.")
            score = min(score, 0.1)

    return round(_clamp(score), 3), warnings


def aggregate(components: list[ScoreComponent], integration_score: float, hard_fail: bool) -> float:
    if hard_fail:
        return 0.0
    by_name = {c.name: c.score for c in components}
    total = sum(WEIGHTS[k] * by_name.get(k, 0.0) for k in WEIGHTS if k != "integration")
    total += WEIGHTS["integration"] * integration_score
    return round(_clamp(total), 3)
