# Implementation Plan

## TL;DR

Do not build the pipeline yet. After approval, create a thin Python/Cog skeleton that accepts ALD precursor screening requests, returns mocked ranked results, and is shaped so UMA/OMat24/OMol25 model calls can be swapped in incrementally. The scientific work should proceed as calibration-driven model integration, not as a one-shot claim that an ML potential replaces DFT for all ALD chemistry.

## Phase 0: Repo And Decision Setup

Status: planning only.

Deliverables:

- Private GitHub repo.
- Collaborator access for `paritoshk`.
- README explaining motivation, architecture, and approval gate.
- This plan file.

Approval questions:

- Repo name and owner are acceptable.
- Replicate is acceptable as the first hosted deployment target.
- MVP should prioritize JSON/API correctness over UI polish.
- First films to support: recommended `HfO2`, `TiN`, and `Al2O3`.
- First candidate examples: known precursors plus 3-5 synthetic test candidates.

## Phase 1: Skeleton After Approval

Goal: create an end-to-end shape without scientific implementation risk.

Files likely needed:

- `pyproject.toml`
- `README.md`
- `src/ald_screening/`
- `src/ald_screening/schemas.py`
- `src/ald_screening/scoring.py`
- `src/ald_screening/reporting.py`
- `cog.yaml`
- `predict.py`
- `examples/`
- `tests/`

Behavior:

- Parse a request containing target film, candidate list, co-reactant, surface context, and process constraints.
- Return deterministic mocked scores with the final JSON schema.
- Include tests for schema validation and ranking behavior.
- No real ML claims in this phase.

## Phase 2: Model Spike

Goal: prove one real atomistic calculation can run in the target environment.

Work items:

- Install and load FAIR-Chem/UMA in a controlled environment.
- Run one molecular relaxation or single-point estimate for a known precursor.
- Run one surface or bulk-related calculation relevant to HfO2, TiN, or Al2O3.
- Record model version, task name, device, runtime, input structure, and output energy/force fields.
- Add uncertainty flags when the input chemistry is outside the model's expected domain.

Exit criteria:

- One reproducible script or notebook-equivalent command.
- One JSON result attached to a candidate scorecard.
- Clear limitations documented.

## Phase 3: ALD Screening Heuristics

Goal: turn raw model outputs and descriptors into useful ALD triage.

Score components:

- Delivery: volatility proxy, molecular mass, coordination environment, known hazard flags.
- Stability: decomposition proxy, weak bond alerts, temperature window compatibility.
- Adsorption: candidate/surface interaction energy and plausible reactive site.
- Ligand removal: likely leaving groups and residue risk, especially carbon.
- Self-limiting behavior: steric saturation and reactive site exhaustion proxy.
- Byproducts: volatility, corrosiveness, etching risk.

Implementation notes:

- Keep each score separate before computing an overall rank.
- Preserve evidence fields so users can see why a candidate moved up or down.
- Mark "unknown" explicitly instead of pretending all inputs are quantified.

## Phase 4: Replicate Deployment

Goal: expose the screening pipeline as a hosted API.

Planned endpoint:

```json
{
  "film": "HfO2",
  "surface": "gate_stack",
  "co_reactant": "H2O",
  "temperature_max_c": 350,
  "candidates": [
    {
      "name": "TEMAH",
      "structure": "..."
    }
  ]
}
```

Response:

```json
{
  "ranked_candidates": [],
  "warnings": [],
  "model_provenance": {},
  "artifacts": {}
}
```

Operational constraints:

- Read `REPLICATE_API_TOKEN` or equivalent from environment.
- Never commit secrets from `.zshrc`.
- Keep model downloads/cache behavior explicit.
- Add a small test input that can run quickly before pushing.

## Phase 5: Visualization Bridge

Goal: connect to the Opus-built visualization pipeline.

Artifacts to produce:

- `results.json`
- `scores.csv`
- optional molecule/surface render images
- optional trajectory/structure files
- static HTML report if the visualization pipeline expects one

The bridge should not own scientific scoring. It should only consume stable output from the scoring layer.

## Phase 6: Agent Interface

Goal: make the platform callable by Claude Code or other agents.

Interfaces:

- CLI wrapper for local runs.
- Stable JSON schemas.
- Optional MCP tool wrapper after the API stabilizes.

Agent-safe behavior:

- Validate inputs strictly.
- Return machine-readable errors.
- Include provenance and confidence flags.
- Avoid hidden network calls unless explicitly configured.

## Known Risks

- ML interatomic potentials may fail on exotic organometallics, charged species, transition states, or ALD-specific surfaces.
- OMol25/OMat24/UMA coverage does not guarantee correct precursor decomposition or ligand elimination pathways.
- Volatility, safety, shelf life, and process practicality need external chemical knowledge beyond atomistic energy estimates.
- Replicate may be convenient for demos but not ideal for heavy GPU chemistry workloads or large model caches.
- A good screening platform must identify when it does not know.

## First Approved Coding Task

Recommended first task after approval:

Create the repo skeleton with a mocked scorer, typed schemas, sample HfO2/TiN/Al2O3 requests, tests, and a Cog-compatible `predict.py`. Do not integrate FAIR-Chem or deploy to Replicate until the mock API shape is reviewed.
