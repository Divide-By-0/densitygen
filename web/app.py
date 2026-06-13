"""DensityGen web app: a public, try-it API + UI for ALD precursor screening
and inverse design.

Runs the fast descriptor scorer per request (instant, safe to expose). The
heavy real-MLIP path (UMA/CHGNet) stays on the CLI -- it is too slow / abusable
to run on every public request. Interconnect bucket results are precomputed once
at startup.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

from densitygen.data import CO_REACTANTS, FILMS, KNOWN_PRECURSORS, KNOWN_RECIPES
from densitygen.design import design
from densitygen.interconnects import (
    HAVE_PRECURSORS, NEED_PRECURSORS, run_design_bucket, run_test_bucket)
from densitygen.schemas import Candidate, ScreeningRequest
from densitygen.screen import screen

HERE = Path(__file__).parent
app = FastAPI(title="DensityGen", docs_url="/api/docs")


# ---- request bodies -------------------------------------------------------
class CandidateIn(BaseModel):
    name: str
    formula: str | None = None


class ScreenIn(BaseModel):
    film: str
    candidates: list[CandidateIn]
    co_reactant: str | None = None
    temperature_max_c: float | None = None
    forbidden_elements: list[str] = []


class DesignIn(BaseModel):
    film: str
    co_reactant: str | None = None
    temperature_max_c: float | None = None
    top_n: int = 10


# ---- API ------------------------------------------------------------------
@app.get("/api/meta")
def meta():
    return {
        "films": [
            {"formula": f.formula, "name": f.name, "kind": f.kind,
             "film_element": f.film_element, "role": f.role,
             "co_reactants": list(f.typical_coreactants)}
            for f in FILMS.values()
        ],
        "co_reactants": [{"name": c.name, "role": c.role} for c in CO_REACTANTS.values()],
        "known_precursors": [
            {"name": p.name, "formula": p.formula, "film_element": p.film_element}
            for p in KNOWN_PRECURSORS.values()
        ],
        "recipes": [
            {"precursor": r.precursor, "co_reactant": r.co_reactant, "film": r.film}
            for r in KNOWN_RECIPES
        ],
    }


@app.post("/api/screen")
def api_screen(body: ScreenIn):
    req = ScreeningRequest(
        film=body.film,
        candidates=[Candidate(name=c.name, formula=c.formula) for c in body.candidates],
        co_reactant=body.co_reactant or None,
        temperature_max_c=body.temperature_max_c,
        forbidden_elements=body.forbidden_elements,
        use_ml_potential=False,
    )
    return JSONResponse(screen(req).model_dump())


@app.post("/api/design")
def api_design(body: DesignIn):
    resp = design(
        film=body.film, co_reactant=body.co_reactant,
        temperature_max_c=body.temperature_max_c, top_n=min(body.top_n, 20),
        use_ml_potential=False)
    return JSONResponse(resp.model_dump())


@lru_cache(maxsize=1)
def _interconnects_cached():
    have = []
    for t in HAVE_PRECURSORS:
        have.append({"film": t.film, "why": t.why, "co_reactant": t.co_reactant,
                     "result": run_test_bucket(t).model_dump()})
    need = []
    for t in NEED_PRECURSORS:
        need.append({"film": t.film, "why": t.why, "note": t.note,
                     "co_reactant": t.co_reactant,
                     "result": run_design_bucket(t, top_n=6).model_dump()})
    return {"have_precursors": have, "need_precursors": need}


@app.get("/api/interconnects")
def api_interconnects():
    return JSONResponse(_interconnects_cached())


# ---- static UI ------------------------------------------------------------
@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
