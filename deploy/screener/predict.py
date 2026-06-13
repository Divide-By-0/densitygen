"""Replicate Cog predictor: the DensityGen ALD screener as a hosted API.

Accepts a screening request (target film, candidate precursors, co-reactant,
constraints) and returns the ranked scorecard JSON. This is the agent-callable
endpoint -- Claude Code or any client can POST candidates and get back a
prioritized list of which precursors to pursue.
"""

from __future__ import annotations

import json
from typing import Optional

from cog import BasePredictor, Input

# When pushed, the densitygen package is installed/vendored into the image
# (see deploy note in README). For local `cog predict` from the repo root,
# PYTHONPATH=../../src makes this import resolve.
from densitygen.reporting import render_report
from densitygen.schemas import ScreeningRequest
from densitygen.screen import screen


class Predictor(BasePredictor):
    def setup(self) -> None:
        pass

    def predict(
        self,
        film: str = Input(description="Target film, e.g. 'W', 'Al2O3', 'HfO2', 'TiN'"),
        candidates_json: str = Input(
            description='JSON list of candidates, e.g. '
            '[{"name":"WF6"},{"name":"WCl6","formula":"WCl6"}]'
        ),
        co_reactant: str = Input(description="Co-reactant, e.g. H2O/O3/NH3/B2H6", default=""),
        temperature_max_c: float = Input(description="Process temperature ceiling (C)", default=0.0),
        forbidden_elements: str = Input(description="Comma-separated elements to exclude", default=""),
        use_ml_potential: bool = Input(
            description="Call the hosted UMA model for real atomistic energies", default=False
        ),
    ) -> dict:
        req = ScreeningRequest(
            film=film,
            candidates=json.loads(candidates_json),
            co_reactant=co_reactant or None,
            temperature_max_c=temperature_max_c or None,
            forbidden_elements=[e.strip() for e in forbidden_elements.split(",") if e.strip()],
            use_ml_potential=use_ml_potential,
        )
        resp = screen(req)
        out = resp.model_dump()
        out["report_text"] = render_report(resp)
        return out
