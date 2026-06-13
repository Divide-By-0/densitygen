# DensityGen: ML-Accelerated ALD Precursor Screening

DensityGen tells a chemist **which precursors to prioritize for a target ALD
film**, fast. It runs a seven-axis viability scorecard over candidate precursor
molecules and ranks them, escalating only the survivors to real atomistic
physics (Meta FAIR's **UMA** universal interatomic potential, hosted on
Replicate) and finally to DFT/experiment. The goal is not to replace expert
judgment with a lookup table — it is to make the expensive candidate-triage loop
seconds instead of weeks.

> **Status: built and runnable.** The repo now contains a working package,
> CLI, test suite, example requests, and Replicate/Cog deploy specs. (The
> earlier plan is preserved in `PLAN.md`.)

## Which AI model does the simulation

**Primary: Meta FAIR UMA (`uma-s-1p2`) via `fairchem-core` v2.** It is the SOTA
universal ML interatomic potential — energies/forces on any structure in
seconds on one GPU, replacing DFT runs that take hours-to-days on a
supercomputer. One model, three task heads we map onto ALD questions:

| UMA task head | Computes | ALD question |
|---|---|---|
| `oc20` | adsorption energy on a slab | Does it chemisorb? Is it self-limiting? |
| `omol` | molecular / ligand energetics | Stability, ligand-bond strength, clean removal |
| `omat` | bulk/surface formation energy | Is the film/byproduct thermodynamically favorable? |

**Backend chain (auto-selected by `get_backend()`):**

1. **Local UMA** (`fairchem-core`, `uma-s-1p2`) — preferred. *Gated on
   HuggingFace*: needs an `HF_TOKEN` that has been granted access to
   `facebook/UMA`. The pipeline is verified to run right up to that wall (builds
   ASE structures, loads fairchem, attempts the gated weight download).
2. **Hosted UMA on Replicate** — the Cog model in `deploy/uma/` (set
   `DENSITYGEN_UMA_MODEL`).
3. **CHGNet** (ungated, ships its own weights) — the backend that **actually
   runs in this environment today** and produces real energies offline
   (e.g. WF₆ = −43.47 eV, MoF₆ = −40.07 eV). It is a *materials* potential, so
   it is trustworthy for slabs/bulk and a labeled *proxy* for isolated precursor
   molecules — never overclaimed.
4. **Descriptor scorer** (no ML) — always-available fallback so the tool works
   with zero heavy deps.

So UMA is the configured primary; because its weights are gated, an **ungated
universal MLIP (CHGNet)** computes the real numbers here, on the exact same
`ase.Atoms` interface. Swapping in UMA is a token-access change, not a code
change.

**Key finding:** *nothing chemistry-related is pre-hosted on Replicate* — its
catalog is media/LLM generation only. "Best model on Replicate" therefore means
**we deploy UMA ourselves via Cog** (`deploy/uma/`).

## Quickstart

```bash
pip install -e .                      # core: pydantic + numpy; runs immediately
ald-screen demo                       # the WF6 -> W headline case
ald-screen recipes                    # the known-good calibration set
ald-screen run examples/wf6_w.json    # full ranked scorecard

# Inverse design: PROPOSE novel precursors you never listed
ald-screen design --film W --co-reactant B2H6 --temperature-max-c 350

# Interconnect demo: screen materials that have precursors, design ones that don't
ald-screen interconnects

# Real ML-potential energies (UMA if you have access, else CHGNet fallback):
pip install -e .[ml]                  # fairchem-core + ase + chgnet
ald-screen demo --uma
ald-screen interconnects --uma
```

### Real ML-potential compute (verified)

`--uma` runs an actual interatomic potential. UMA needs HuggingFace access to
`facebook/UMA`; without it the tool auto-falls-back to **CHGNet** (ungated) and
still computes real energies — e.g. `ald-screen demo --uma` returns WF₆'s real
molecular energy (−43.47 eV) and a real adsorption energy on a W slab, each axis
tagged `✓ measured` (UMA) or `~ estimated` (proxy MLIP).

Python API:

```python
from densitygen import screen, ScreeningRequest, Candidate

resp = screen(ScreeningRequest(
    film="W", co_reactant="B2H6", temperature_max_c=350,
    candidates=[Candidate(name="WF6"), Candidate(name="WCl6", formula="WCl6")],
))
print(resp.ranked_candidates[0].name, resp.ranked_candidates[0].overall_score)
```

## The scorecard

Every candidate gets seven components, each with an **evidence string** and a
**confidence tag** (`✓ measured` / `~ estimated` / `? unknown`), plus hard gates:

- `delivery` — volatility / can it be delivered as vapor
- `thermal_window` — survives the line and has a self-limiting window at the cap
- `surface_reactivity` — chemisorbs / exchanges on the target surface (UMA `oc20`)
- `self_limiting` — steric saturation stops growth after one layer
- `clean_ligand` — carbon / halide residue risk
- `byproduct` — benign vs. etching/corrosive (e.g. HF from fluorides)
- `integration` — **hard gates**: must contain the film element; honors
  `forbidden_elements`

A precursor that cannot deliver the film's payload element **hard-fails to 0** —
no amount of volatility saves a molecule with no tungsten in it. Each candidate
ends with a `recommended_next_step` that enforces the escalation ladder
(descriptor → UMA → DFT → experiment).

### Calibration against known recipes

The tool is validated against literature ALD systems (the regression set in
`tests/test_screen.py`): WF6→W, TMA→Al2O3, TEMAH/HfCl4→HfO2, TiCl4/TDMAT→TiN.
`ald-screen demo` shows WF6 ranking #1 for tungsten while honestly flagging its
HF-byproduct weakness — the real-world integration headache.

## Inverse design — proposing precursors that don't exist yet

`ald-screen design --film <X>` doesn't screen a list you provide — it
*generates* one. It combinatorially assembles the film's metal with a curated
ligand library (halides, alkyls, alkylamides, alkoxides, hydride, carbonyl, plus
heteroleptic mixes), scores every proposal with the same scorecard, and ranks
them. Cheap descriptors triage the whole combinatorial set; UMA confirms only
the top survivors (the escalation ladder). As a built-in sanity check, the loop
re-derives WF₆ for tungsten and flags it ★ — evidence the search space is sane.

## Interconnect-resistance demo (`ald-screen interconnects`)

The end-to-end demonstration on a real frontier problem — replacing Cu/W in
scaled interconnects, where resistivity explodes from electron scattering. Two
buckets:

- **Bucket A — materials that have precursors** (Ru, Mo, Co): screened
  end-to-end with real candidate precursors (Ru(EtCp)₂, MoO₂Cl₂, CoCp₂, …). This
  exercises the full flow on known chemistry.
- **Bucket B — materials with no mature ALD precursor** (NbP, MoP, CoSi, NbAs —
  topological semimetals / intermetallics): the inverse-design loop *proposes*
  precursors and produces ranked results where no recipe exists.

## Deploying the UMA model to Replicate

```bash
cd deploy/uma
cog login
cog push r8.im/<your-username>/uma-ald          # GPU image, fairchem + UMA
```

UMA weights are gated on HuggingFace, so set `HF_TOKEN` as a **Replicate
secret** (the predictor downloads weights at cold start, not at build time — the
build env has no secrets and baking gated weights in violates the HF license).
Then point the screener at it:

```bash
export DENSITYGEN_UMA_MODEL=<your-username>/uma-ald
ald-screen run examples/wf6_w.json --uma
```

The screener API itself can also be hosted (CPU) via `deploy/screener/` so
agents/UIs can POST candidates and get back the ranked JSON.

## Architecture

```
candidates ─▶ chem.py        formula/SMILES ─▶ composition + descriptors
           ─▶ data/          curated precursor / film / recipe ground truth
           ─▶ scoring.py     7 score components + hard gates
           ─▶ compute.py     UMA-on-Replicate energies (oc20/omol/omat)  ◀─ optional
           ─▶ screen.py      orchestrate ─▶ ranked scorecard
           ─▶ reporting.py   text report + CSV   |  cli.py  |  deploy/*  (Cog)
```

The seam that matters: `compute.py` (physics) is fully decoupled from
`scoring.py` (ALD logic), so the same screener runs on free descriptors today
and transparently upgrades to real UMA energies once the Cog model is live.

## What this does *not* claim

- ML potentials can be wrong on exotic organometallics, charged species, and
  transition states — every score carries provenance and an uncertainty tag.
- Volatility, shelf life, cost, and safety need chemical knowledge beyond
  atomistic energies; the tool flags `unknown` instead of inventing numbers.
- A good screen's job is to know what it does not know and say so.

See `SAMPLE_QUERIES.md` for the chemist questions this is built to answer, and
`PLAN.md` for the original phased plan and references.
