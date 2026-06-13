"""Interconnect-resistance materials: the two-bucket final demonstration.

The back-end-of-line interconnect problem: as wires scale below ~20 nm, Cu/W
effective resistivity rises sharply (electron surface + grain-boundary
scattering) and the required diffusion barriers stop scaling. The fix is
alternative metals/compounds with a short electron mean free path and
barrierless integration.

This module splits the candidate materials exactly as the user framed it:

  Bucket A -- materials that DO have established ALD precursors. We screen real
              candidate precursors against them: an end-to-end test of the
              screening flow on known chemistry.

  Bucket B -- materials that do NOT yet have a mature ALD precursor (topological
              semimetals, intermetallics). We run the inverse-design loop to
              PROPOSE precursors: a discovery demo that produces results where
              no recipe exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from densitygen.design import design
from densitygen.schemas import Candidate, ScreeningRequest, ScreeningResponse
from densitygen.screen import screen


@dataclass(frozen=True)
class InterconnectTarget:
    film: str
    has_precursor: bool
    why: str                       # resistivity / integration rationale
    co_reactant: str
    temperature_max_c: float
    test_candidates: list[str] = field(default_factory=list)  # for bucket A
    note: str = ""


# Bucket A: established-precursor interconnect metals -> end-to-end screening tests.
HAVE_PRECURSORS: list[InterconnectTarget] = [
    InterconnectTarget(
        film="Ru", has_precursor=True, co_reactant="O2 plasma", temperature_max_c=325,
        why="Ru has a short electron mean free path (~6.6 nm) and can run barrierless; "
            "leading Cu-replacement for scaled lines/vias.",
        test_candidates=["Ru(EtCp)2", "RuCp2", "RuCl3"],
        note="Ru(EtCp)2 is the industry workhorse; RuCl3 is a non-volatile foil."),
    InterconnectTarget(
        film="Mo", has_precursor=True, co_reactant="H2 plasma", temperature_max_c=400,
        why="Mo resistivity stays low at nanoscale and tolerates high current density; "
            "adopted for buried power rails / scaled interconnect.",
        test_candidates=["MoO2Cl2", "Mo(CO)6", "MoF6", "MoCl5"],
        note="MoO2Cl2/Mo(CO)6 avoid the HF of MoF6."),
    InterconnectTarget(
        film="Co", has_precursor=True, co_reactant="H2 plasma", temperature_max_c=300,
        why="Co was the first sub-Cu liner/fill metal in production at scaled nodes; "
            "good gap-fill and EM resistance.",
        test_candidates=["CoCp2", "Co(NMe2)3"],
        note="CoCp2 (cobaltocene) is established; Co(NMe2)3 is an amide alternative."),
]

# Bucket B: emerging interconnect materials WITHOUT a mature ALD precursor ->
# inverse-design demos. (PH3/AsH3/SiH4 supply the non-metal from the gas phase;
# the unsolved problem is a volatile single-source precursor for the METAL.)
NEED_PRECURSORS: list[InterconnectTarget] = [
    InterconnectTarget(
        film="NbP", has_precursor=False, co_reactant="PH3", temperature_max_c=400,
        why="Topological Weyl semimetal; theory predicts resistivity that DROPS at "
            "nanoscale (surface-state conduction) — opposite to Cu. No ALD route exists.",
        note="Propose a volatile Nb precursor; P from PH3."),
    InterconnectTarget(
        film="MoP", has_precursor=False, co_reactant="PH3", temperature_max_c=450,
        why="Low-resistivity phosphide interconnect candidate; no mature ALD precursor.",
        note="Propose a volatile Mo precursor; P from PH3."),
    InterconnectTarget(
        film="CoSi", has_precursor=False, co_reactant="SiH4", temperature_max_c=400,
        why="Intermetallic monosilicide with low resistivity and good contact behavior; "
            "no established single-source ALD route.",
        note="Propose a volatile Co precursor; Si from SiH4."),
    InterconnectTarget(
        film="NbAs", has_precursor=False, co_reactant="AsH3", temperature_max_c=400,
        why="Weyl semimetal interconnect candidate; entirely undeveloped for ALD.",
        note="Propose a volatile Nb precursor; As from AsH3."),
]


def run_test_bucket(target: InterconnectTarget, use_ml_potential: bool = False) -> ScreeningResponse:
    """Bucket A: screen real candidate precursors for an established material."""
    return screen(ScreeningRequest(
        film=target.film,
        co_reactant=target.co_reactant,
        temperature_max_c=target.temperature_max_c,
        use_ml_potential=use_ml_potential,
        candidates=[Candidate(name=n) if _is_known(n) else _as_candidate(n)
                    for n in target.test_candidates],
    ))


def run_design_bucket(target: InterconnectTarget, use_ml_potential: bool = False,
                      top_n: int = 8) -> ScreeningResponse:
    """Bucket B: propose precursors for a material that has none."""
    return design(
        film=target.film,
        co_reactant=target.co_reactant,
        temperature_max_c=target.temperature_max_c,
        top_n=top_n,
        use_ml_potential=use_ml_potential,
    )


# --- small helpers so unknown candidate names still resolve to a formula -----
_FORMULA_HINTS = {"RuCl3": "RuCl3", "Co(NMe2)3": "Co[N(CH3)2]3", "MoCl5": "MoCl5",
                  "MoF6": "MoF6"}


def _is_known(name: str) -> bool:
    from densitygen.data import lookup_precursor
    return lookup_precursor(name) is not None


def _as_candidate(name: str) -> Candidate:
    return Candidate(name=name, formula=_FORMULA_HINTS.get(name))
