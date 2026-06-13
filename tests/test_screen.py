"""Regression tests: the screener must rank known-good precursors at the top
for their film, hard-fail precursors that can't deliver the film element, and
honor forbidden-element gates."""

import pytest

from densitygen import Candidate, ScreeningRequest, screen
from densitygen.data import KNOWN_RECIPES


def _names_in_rank_order(resp):
    return [c.name for c in resp.ranked_candidates]


def test_wf6_ranks_first_for_tungsten():
    resp = screen(ScreeningRequest(
        film="W", co_reactant="B2H6", temperature_max_c=350,
        candidates=[Candidate(name="WF6"), Candidate(name="WCl6", formula="WCl6"),
                    Candidate(name="TMA")],
    ))
    assert _names_in_rank_order(resp)[0] == "WF6"
    assert resp.ranked_candidates[0].is_known_recipe


def test_precursor_without_film_element_hard_fails():
    resp = screen(ScreeningRequest(
        film="W", candidates=[Candidate(name="TMA")],
    ))
    r = resp.ranked_candidates[0]
    assert r.overall_score == 0.0
    assert any("HARD FAIL" in w for w in r.warnings)


def test_forbidden_element_penalized():
    resp = screen(ScreeningRequest(
        film="HfO2", co_reactant="H2O", forbidden_elements=["Cl"],
        candidates=[Candidate(name="HfCl4"), Candidate(name="TEMAH")],
    ))
    by = {c.name: c for c in resp.ranked_candidates}
    assert any("forbidden element Cl" in w for w in by["HfCl4"].warnings)
    # The halide-free alkylamide should win when Cl is forbidden.
    assert _names_in_rank_order(resp)[0] == "TEMAH"


def test_wf6_byproduct_is_the_weak_axis():
    # The scorer should surface HF byproduct as WF6's worst component -- this is
    # the real-world integration headache and a good honesty check.
    resp = screen(ScreeningRequest(film="W", co_reactant="B2H6", candidates=[Candidate(name="WF6")]))
    comps = {c.name: c.score for c in resp.ranked_candidates[0].components}
    assert comps["byproduct"] == min(comps.values())


@pytest.mark.parametrize("recipe", [r for r in KNOWN_RECIPES])
def test_known_recipe_scores_well(recipe):
    # Every literature recipe's canonical precursor should land in the "promote"
    # band (>= 0.6) for its film -- if it doesn't, the heuristics are miscalibrated.
    resp = screen(ScreeningRequest(
        film=recipe.film, co_reactant=recipe.co_reactant,
        candidates=[Candidate(name=recipe.precursor)],
    ))
    r = resp.ranked_candidates[0]
    assert r.overall_score >= 0.6, f"{recipe.precursor}->{recipe.film} scored {r.overall_score}"


def test_provenance_local_by_default():
    resp = screen(ScreeningRequest(film="W", candidates=[Candidate(name="WF6")]))
    assert resp.model_provenance.compute_backend == "local-descriptors"
