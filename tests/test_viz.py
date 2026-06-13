"""Tests for the viz bridge: the screening-output -> display data contract and
the bundle writer. These guard the seam the user cares about most -- that what
the UI renders is exactly what the pipeline computed."""

from __future__ import annotations

import json

from densitygen import Candidate, ScreeningRequest, screen
from densitygen.viz import (
    COMPONENT_ORDER,
    default_suggestions,
    response_to_payload,
    write_bundle,
)


def _resp():
    req = ScreeningRequest(
        film="HfO2", co_reactant="H2O", temperature_max_c=300,
        forbidden_elements=["Cl"],
        candidates=[Candidate(name="TEMAH"), Candidate(name="HfCl4")],
    )
    return screen(req), req


def test_payload_contract_mirrors_pipeline():
    resp, req = _resp()
    payload = response_to_payload(resp, request=req)

    # meta carries the request context + provenance the UI needs.
    meta = payload["meta"]
    assert meta["film"] == "HfO2"
    assert meta["co_reactant"] == "H2O"
    assert meta["forbidden_elements"] == ["Cl"]
    assert meta["component_order"] == COMPONENT_ORDER
    assert "compute_backend" in meta["provenance"]

    # candidates are ranked, carry the raw scores (no pre-baked display fields),
    # and every component name is present so the UI never invents a value.
    cands = payload["candidates"]
    assert [c["rank"] for c in cands] == list(range(1, len(cands) + 1))
    scores = [c["overall_score"] for c in cands]
    assert scores == sorted(scores, reverse=True)
    for c in cands:
        names = [comp["name"] for comp in c["components"]]
        assert names == COMPONENT_ORDER
        for comp in c["components"]:
            assert 0.0 <= comp["score"] <= 1.0
            assert comp["confidence"] in ("measured", "estimated", "unknown")


def test_payload_values_match_response_exactly():
    """The display payload must not perturb any computed number."""
    resp, req = _resp()
    payload = response_to_payload(resp, request=req)
    for raw, out in zip(resp.ranked_candidates, payload["candidates"]):
        assert out["name"] == raw.name
        assert out["overall_score"] == raw.overall_score
        assert out["formula"] == raw.formula
        raw_scores = {c.name: c.score for c in raw.components}
        out_scores = {c["name"]: c["score"] for c in out["components"]}
        assert raw_scores == out_scores


def test_suggestions_are_film_appropriate():
    sug = default_suggestions("HfO2", "Hf")
    assert sug and all(isinstance(s, str) for s in sug)
    # Unknown metal still yields sensible formula-shaped fallbacks.
    assert default_suggestions("Xx9", "Xx")


def test_write_bundle_is_self_contained(tmp_path):
    resp, req = _resp()
    payload = response_to_payload(resp, request=req)
    entry = write_bundle(payload, tmp_path)

    assert entry.name == "densitygen.dc.html"
    for f in ("densitygen.dc.html", "support.js", "data.js"):
        assert (tmp_path / f).is_file()

    data_js = (tmp_path / "data.js").read_text()
    assert data_js.startswith("// GENERATED")
    assert "window.DENSITYGEN_DATA = " in data_js
    # The embedded blob must be valid JSON matching the payload.
    blob = data_js.split("window.DENSITYGEN_DATA = ", 1)[1].rsplit(";", 1)[0]
    assert json.loads(blob)["meta"]["film"] == "HfO2"
