"""Tests for the inverse-design loop and the interconnect two-bucket demo."""

import pytest

from densitygen.design import design, generate, METAL_OXIDATION
from densitygen.interconnects import (
    HAVE_PRECURSORS, NEED_PRECURSORS, run_design_bucket, run_test_bucket)


def test_generate_produces_homoleptic_and_mixed():
    props = generate("W", 6)
    formulas = {f for f, _, _ in props}
    assert any("F" in f for f in formulas)         # WF6-like
    assert any(c.count("W") == 1 for _, c, _ in props)
    assert len(props) > 5


def test_design_rediscovers_known_precursor_for_tungsten():
    # Sanity check: the generative search should re-derive a real recipe (WF6).
    resp = design(film="W", top_n=30)
    assert any(r.is_known_recipe for r in resp.ranked_candidates), \
        "inverse design failed to rediscover any known W precursor"


def test_design_all_proposals_deliver_the_metal():
    resp = design(film="Nb", top_n=10)
    assert resp.ranked_candidates
    for r in resp.ranked_candidates:
        assert r.origin == "proposed"
        assert r.film_element == "Nb"
        assert r.overall_score > 0  # none should hard-fail (all contain Nb)


@pytest.mark.parametrize("target", HAVE_PRECURSORS)
def test_bucket_a_screens_known_materials(target):
    resp = run_test_bucket(target)
    assert resp.ranked_candidates
    # The winner must actually deliver the film's metal.
    assert resp.ranked_candidates[0].film_element == \
        {"Ru": "Ru", "Mo": "Mo", "Co": "Co"}[target.film]


@pytest.mark.parametrize("target", NEED_PRECURSORS)
def test_bucket_b_designs_for_materials_without_precursors(target):
    assert target.has_precursor is False
    resp = run_design_bucket(target, top_n=6)
    assert resp.ranked_candidates, f"no proposals generated for {target.film}"
    assert all(r.origin == "proposed" for r in resp.ranked_candidates)
