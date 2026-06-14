"""DensityGen web app: public try-it API + UI for ALD precursor screening,
inverse design, and the rich DataCore results dashboard.

Runs the fast descriptor scorer by default (instant, safe to expose). The real
MLIP path is available as an explicit, capped Replicate UMA mode so users can
see the atomistic calculation without accidentally spending GPU budget on bulk
requests.

Two result surfaces:
  * the lightweight built-in cards (index.html), and
  * the Fable "DataCore" dashboard (Pareto front + 7-axis radar) at /viz, which
    is the polished view for final results. The DC component is served with its
    data injected server-side and a live re-rank endpoint at /dc/api/screen.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import importlib.util
from densitygen.compute import get_backend, REPLICATE_HARDWARE, REPLICATE_RATE_USD_PER_SECOND
from densitygen.data import CO_REACTANTS, FILMS, KNOWN_PRECURSORS, KNOWN_RECIPES, lookup_film
from densitygen.design import design
from densitygen.interconnects import (
    HAVE_PRECURSORS, NEED_PRECURSORS, run_design_bucket, run_test_bucket)
from densitygen.schemas import Candidate, ScreeningRequest
from densitygen.screen import screen
from densitygen.viz import response_to_payload

HERE = Path(__file__).parent
VIZ_ASSETS = Path(__import__("densitygen").__file__).parent / "viz_assets"
app = FastAPI(title="DensityGen", docs_url="/api/docs")
MAX_REAL_CANDIDATES = 4


@lru_cache(maxsize=1)
def _installed_real_backend() -> str | None:
    """Name of the best real ML-potential backend installed on this server.

    Uses `find_spec` (and env, for the hosted route) so it never imports torch
    at startup -- it only reports what *could* run, matching get_backend()'s
    preference order. The actual engine is loaded lazily on the first real call.
    """
    if os.environ.get("REPLICATE_API_TOKEN") and os.environ.get("DENSITYGEN_UMA_MODEL"):
        return "uma-replicate"
    if importlib.util.find_spec("fairchem") is not None:
        return "uma-local"
    if importlib.util.find_spec("mace") is not None:
        return "mace-mp-0"
    if importlib.util.find_spec("chgnet") is not None:
        return "chgnet"
    return None


def default_co_reactant(film: str, given: str | None) -> str | None:
    """Auto-pick a co-reactant when the user doesn't give one.

    The film *kind* fixes the chemistry: oxide -> oxidant, nitride -> nitridant,
    metal -> reductant. ``typical_coreactants`` is curated in priority order, so
    the first entry is the sensible default (e.g. W -> SiH4, Al2O3 -> H2O).
    """
    if given:
        return given
    f = lookup_film(film)
    return f.typical_coreactants[0] if f and f.typical_coreactants else None


# ---- request bodies -------------------------------------------------------
class CandidateIn(BaseModel):
    name: str
    formula: str | None = None
    smiles: str | None = None


class ScreenIn(BaseModel):
    film: str
    candidates: list[CandidateIn]
    co_reactant: str | None = None
    temperature_max_c: float | None = None
    forbidden_elements: list[str] = []
    use_ml_potential: bool = False


class DesignIn(BaseModel):
    film: str
    co_reactant: str | None = None
    temperature_max_c: float | None = None
    top_n: int = 10


# ---- metadata for the UI --------------------------------------------------
@app.get("/api/meta")
def meta():
    return {
        "films": [
            {"formula": f.formula, "name": f.name, "kind": f.kind,
             "film_element": f.film_element, "role": f.role,
             "co_reactants": list(f.typical_coreactants),
             "default_co_reactant": (f.typical_coreactants[0] if f.typical_coreactants else None)}
            for f in FILMS.values()
        ],
        "co_reactants": [{"name": c.name, "role": c.role, "notes": c.notes}
                         for c in CO_REACTANTS.values()],
        "known_precursors": [
            {"name": p.name, "formula": p.formula, "film_element": p.film_element}
            for p in KNOWN_PRECURSORS.values()
        ],
        "recipes": [
            {"precursor": r.precursor, "co_reactant": r.co_reactant, "film": r.film}
            for r in KNOWN_RECIPES
        ],
        "simulation": {
            "max_real_candidates": MAX_REAL_CANDIDATES,
            "hardware": REPLICATE_HARDWARE,
            "rate_usd_per_second": REPLICATE_RATE_USD_PER_SECOND,
            "replicate_model": os.environ.get("DENSITYGEN_UMA_MODEL"),
            "replicate_configured": bool(
                os.environ.get("REPLICATE_API_TOKEN") and os.environ.get("DENSITYGEN_UMA_MODEL")
            ),
            # Which real ML-potential backend is actually available, so the UI can
            # show honest copy (CHGNet = local/free/proxy vs hosted UMA = $/sec).
            "real_backend": _installed_real_backend(),
        },
    }


# ---- raw scoring API (used by the built-in cards) -------------------------
def _real_backend_or_error(body: ScreenIn):
    if not body.use_ml_potential:
        return None
    if len(body.candidates) > MAX_REAL_CANDIDATES:
        return JSONResponse(
            {"error": f"Real simulation is capped at {MAX_REAL_CANDIDATES} candidates per call."},
            status_code=400,
        )
    # Use the full backend chain (local UMA -> hosted UMA on Replicate -> MACE ->
    # CHGNet). Real simulation works whenever ANY real engine is reachable -- it
    # no longer hard-requires the Replicate UMA model. CHGNet ships its weights in
    # the pip package, so the hosted demo runs real ML-potential energies offline.
    backend = get_backend()
    if backend is None:
        return JSONResponse(
            {"error": "No ML-potential backend is available on this server. "
                      "Install the `chgnet` engine (ungated, offline), or set "
                      "DENSITYGEN_UMA_MODEL + REPLICATE_API_TOKEN for hosted UMA."},
            status_code=503,
        )
    return backend


def _run_screen(body: ScreenIn):
    backend = _real_backend_or_error(body)
    if isinstance(backend, JSONResponse):
        return backend
    return screen(ScreeningRequest(
        film=body.film,
        candidates=[Candidate(name=c.name, formula=c.formula, smiles=c.smiles) for c in body.candidates],
        co_reactant=default_co_reactant(body.film, body.co_reactant),
        temperature_max_c=body.temperature_max_c,
        forbidden_elements=body.forbidden_elements,
        use_ml_potential=body.use_ml_potential,
    ), backend=backend)


@app.post("/api/screen")
def api_screen(body: ScreenIn):
    resp = _run_screen(body)
    if isinstance(resp, JSONResponse):
        return resp
    return JSONResponse(resp.model_dump())


@app.post("/api/design")
def api_design(body: DesignIn):
    resp = design(
        film=body.film, co_reactant=default_co_reactant(body.film, body.co_reactant),
        temperature_max_c=body.temperature_max_c, top_n=min(body.top_n, 20),
        use_ml_potential=False)
    return JSONResponse(resp.model_dump())


# ---- DataCore dashboard (the rich results view) ---------------------------
def _coerce_candidates(raw) -> list[Candidate]:
    """Accept candidates as dicts, plain names, or 'name|formula' strings (the
    UI's compact encoding for a candidate with an explicit formula)."""
    out = []
    for c in raw or []:
        if isinstance(c, str):
            name, _, formula = c.partition("|")
            out.append(Candidate(name=name.strip(), formula=(formula.strip() or None)))
        elif isinstance(c, dict):
            out.append(Candidate(name=c.get("name") or c.get("formula"),
                                  formula=c.get("formula"), smiles=c.get("smiles")))
    return out


@app.post("/dc/api/screen")
async def dc_screen(request: Request):
    """Live re-rank endpoint the DataCore 'suggest a precursor' input calls.
    Returns the *payload* shape (meta/candidates/suggestions), not the raw
    response, because that is what the DC component renders."""
    body = await request.json()
    req = ScreeningRequest(
        film=body.get("film"),
        candidates=_coerce_candidates(body.get("candidates")),
        co_reactant=default_co_reactant(body.get("film"), body.get("co_reactant")),
        temperature_max_c=body.get("temperature_max_c"),
        forbidden_elements=body.get("forbidden_elements") or [],
        use_ml_potential=False,
    )
    resp = screen(req)
    return JSONResponse(response_to_payload(resp, request=req, mode="screen", api_url="/dc"))


def _dc_page(payload: dict) -> str:
    """Inject a payload into the DC component HTML and fix asset paths so it
    renders standalone from this server (no baked data.js needed)."""
    import json
    html = (VIZ_ASSETS / "densitygen.dc.html").read_text(encoding="utf-8")
    data_script = ("<script>window.DENSITYGEN_DATA = "
                   + json.dumps(payload, ensure_ascii=False) + ";</script>")
    html = html.replace('<script src="./data.js"></script>', data_script)
    html = html.replace('./support.js', '/dc-assets/support.js')
    return html


def _opt_float(v: str | None) -> float | None:
    # REASON: /viz takes its params from the query string, and the UI sends the
    # raw form value -- an empty field arrives as `temperature_max_c=` (""), which
    # a `float` query param rejects with a 422. Treat blank/garbage as "unset".
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _opt_int(v: str | None, default: int) -> int:
    try:
        return int(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


@app.get("/viz", response_class=HTMLResponse)
def viz(film: str = "W", mode: str = "screen", co_reactant: str | None = None,
        temperature_max_c: str | None = None, forbidden: str = "",
        candidates: str = "", top_n: str | None = None):
    """Render the rich DataCore dashboard for a screening or design run."""
    co = default_co_reactant(film, co_reactant or None)
    tmax = _opt_float(temperature_max_c)
    forbid = [e.strip() for e in forbidden.split(",") if e.strip()]
    if mode == "design":
        resp = design(film=film, co_reactant=co, temperature_max_c=tmax,
                      forbidden_elements=forbid, top_n=_opt_int(top_n, 12),
                      use_ml_potential=False)
        payload = response_to_payload(resp, request=None, mode="design", api_url="/dc")
    else:
        cand_names = [c.strip() for c in candidates.split(",") if c.strip()] or ["WF6"]
        req = ScreeningRequest(
            film=film, candidates=_coerce_candidates(cand_names), co_reactant=co,
            temperature_max_c=tmax, forbidden_elements=forbid,
            use_ml_potential=False)
        resp = screen(req)
        payload = response_to_payload(resp, request=req, mode="screen", api_url="/dc")
    return HTMLResponse(_dc_page(payload))


# ---- interconnect demo (precomputed) --------------------------------------
@lru_cache(maxsize=1)
def _interconnects_cached():
    have = [{"film": t.film, "why": t.why, "co_reactant": t.co_reactant,
             "result": run_test_bucket(t).model_dump()} for t in HAVE_PRECURSORS]
    need = [{"film": t.film, "why": t.why, "note": t.note, "co_reactant": t.co_reactant,
             "result": run_design_bucket(t, top_n=6).model_dump()} for t in NEED_PRECURSORS]
    return {"have_precursors": have, "need_precursors": need}


@app.get("/api/interconnects")
def api_interconnects():
    return JSONResponse(_interconnects_cached())


# ---- static UI ------------------------------------------------------------
@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/about")
def about():
    return FileResponse(HERE / "static" / "about.html")


app.mount("/dc-assets", StaticFiles(directory=VIZ_ASSETS), name="dc-assets")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
