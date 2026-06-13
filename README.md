# DensityGen

**A materials-selection copilot for chip R&D.** Pick the right thin-film material — and the precursor to deposit it — for a next-generation chip in an afternoon instead of months.

### Why this matters (non-technical)

Every modern chip — in your phone, in AI data centers, in defense systems — is a stack of *hundreds* of films, each only a few atoms thick, that insulate, conduct, or block. Each new chip generation forces a switch to new materials because the old ones physically stop working. Finding the replacement today takes a specialist **months** of slow, fragile physics simulations, one material at a time — and a wrong pick can blow a multi-year, multi-billion-dollar fab bet. DensityGen compresses that triage loop from weeks to seconds and reserves the expensive simulations for only the final finalists.

**Who it's for:** computational materials scientists and process engineers at semiconductor fabs (Intel, TSMC, Samsung, Applied Materials), defense/aerospace R&D, and the precursor-chemical suppliers (Merck, Entegris, Air Liquide) whose multi-million-dollar bets ride on the choice.

---

## This repo has two parts

| Part | What it is | Stack | Lives in |
| --- | --- | --- | --- |
| **1. Web copilot UI** | The interactive demo — translate a fab spec into a ranked candidate shortlist from **live Materials Project data**, explore trade-offs, and watch surface chemistry in 3D. | Next.js 16 · React 19 · Tailwind v4 · Three.js | `app/`, `components/`, `lib/` |
| **2. Screening engine** | The Python decision engine — a seven-axis ALD-precursor viability scorecard that escalates survivors to a real ML interatomic potential (UMA / CHGNet) and proposes novel precursors via inverse design. | Python · fairchem/UMA · Cog/Replicate | `src/densitygen/`, `deploy/`, `web/` |

The two are complementary demos of the same thesis (fast screening → escalate only the survivors). The web UI talks directly to Materials Project; the engine runs the atomistic physics.

---

# Part 1 — Web copilot UI (Next.js)

Turns the two finished design components into a deployable app wired to the **real Materials Project REST API**.

### Six screens
1. **Intake** — natural-language fab spec → DFT-queryable property targets + hard constraints + periodic search space.
2. **Candidates** — dense, sortable table of **live MP** dielectric-oxide candidates, composite-ranked, with Pareto-front tags.
3. **Trade-offs** — κ×E_g Pareto scatter (real κ from `e_total`), HER Sabatier volcano, constraint explorer.
4. **Compute** — faithful simulation of an atomate2 → SLURM DFT dispatch with custodian convergence handling.
5. **Material** — **real relaxed crystal structure** (rotatable), computed properties, band sketch, provenance.
6. **Surface** — interactive Three.js ALD half-reaction with a hero activation-energy readout and "Confirm with DFT →".

### Real vs. illustrative (honest boundary)
- **Live from Materials Project**: κ, band gap, formation energy, stability, bulk modulus, crystal structure (real `mp-…` IDs). The genuine κ–E_g anticorrelation shows up in the data.
- **Curated** (not in MP): ALD precursor map, HER volcano set.
- **Simulated / authored**: the DFT dispatch table; the 3D surface reaction + activation energy are an MLIP-style illustrative trajectory, clearly labeled *schematic / predicted ±0.08 eV, not DFT-confirmed*.

If `MP_API_KEY` is missing or MP errors, the app **silently falls back** to a bundled candidate set and flags it `CACHED` — so a live demo never fails.

### Run it
```bash
echo "MP_API_KEY=your_key_here" > .env.local   # free key: materialsproject.org/api
npm install
npm run dev    # http://localhost:3000  (runs on the cached set without a key)
```
The MP key is server-side only (`MP_API_KEY`) and never reaches the browser. Deploys to **Vercel** as-is — set `MP_API_KEY` in project env.

---

# Part 2 — ML-Accelerated ALD Precursor Screening (Python)

DensityGen's engine tells a chemist **which precursors to prioritize for a target ALD film**, fast. It runs a seven-axis viability scorecard over candidate precursor molecules and ranks them, escalating only survivors to real atomistic physics (Meta FAIR's **UMA** universal interatomic potential) and finally to DFT/experiment.

> **Status: built and runnable** — working package, CLI, test suite, example requests, and Replicate/Cog deploy specs. The original phased plan is in [`PLAN.md`](PLAN.md); the chemist questions it answers are in [`SAMPLE_QUERIES.md`](SAMPLE_QUERIES.md).

> **Built with Claude Code.** Every human prompt across the build sessions is exported, in order, to [`prompts.md`](prompts.md) — the project's full instruction history.

### Which AI model does the simulation

**Primary: Meta FAIR UMA (`uma-s-1p2`) via `fairchem-core` v2** — a SOTA universal ML interatomic potential: energies/forces on any structure in seconds on one GPU, replacing DFT runs that take hours-to-days. One model, three task heads mapped onto ALD questions:

| UMA task head | Computes | ALD question |
|---|---|---|
| `oc20` | adsorption energy on a slab | Does it chemisorb? Is it self-limiting? |
| `omol` | molecular / ligand energetics | Stability, ligand-bond strength, clean removal |
| `omat` | bulk/surface formation energy | Is the film/byproduct thermodynamically favorable? |

**Backend chain (auto-selected by `get_backend()`):** Local UMA (gated on HuggingFace `facebook/UMA`) → hosted UMA on Replicate (`deploy/uma/`) → **CHGNet** (ungated, runs offline today, e.g. WF₆ = −43.47 eV) → descriptor scorer (no ML, always available). Swapping in UMA is a token-access change, not a code change.

### Quickstart
```bash
pip install -e .                      # core: pydantic + numpy; runs immediately
ald-screen demo                       # the WF6 -> W headline case
ald-screen run examples/wf6_w.json    # full ranked scorecard
ald-screen design --film W --co-reactant B2H6 --temperature-max-c 350   # inverse design
ald-screen interconnects              # Ru/Mo/Co screen + propose precursors where none exist
pip install -e .[ml] && ald-screen demo --uma   # real ML-potential energies (UMA→CHGNet fallback)
```

### The scorecard
Seven components, each with an evidence string and confidence tag (`✓ measured` / `~ estimated` / `? unknown`): `delivery`, `thermal_window`, `surface_reactivity` (UMA `oc20`), `self_limiting`, `clean_ligand`, `byproduct`, `integration` (hard gates — must contain the film element). A precursor with no payload element hard-fails to 0. Calibrated against literature recipes (WF6→W, TMA→Al2O3, TEMAH/HfCl4→HfO2, TiCl4/TDMAT→TiN) in `tests/test_screen.py`. Candidates can be named by their formula (e.g. `WCl6`, `W(CO)6`) — the resolver parses the name when it isn't a curated precursor.

### Visualization
The screening results drive an interactive Fable "DC" dashboard — a ranked scorecard, a Pareto trade-off explorer, the cheap-first escalation ladder, and a per-precursor 7-axis radar with full evidence/provenance. The view never re-implements scoring; it renders exactly what the pipeline computed.
```bash
ald-screen viz examples/wf6_w.json --out densitygen_viz   # bake a self-contained bundle, open densitygen_viz/densitygen.dc.html
ald-screen serve examples/wf6_w.json                       # same, but live: suggest a precursor in the rail -> instant re-rank via /api/screen
```
The right-rail "suggest a precursor" input (with example chips) adds candidates: with `serve` it re-ranks live through the same `screen()`; from the static bundle it queues them and shows the CLI to re-run. The same dashboard is hosted by the web app at `/viz` (`web/app.py`).

### Deploy the UMA model to Replicate
```bash
cd deploy/uma && cog login && cog push r8.im/<your-username>/uma-ald
export DENSITYGEN_UMA_MODEL=<your-username>/uma-ald
ald-screen run examples/wf6_w.json --uma
```
UMA weights are gated, so set `HF_TOKEN` as a **Replicate secret** (downloaded at cold start, not baked into the build). The CPU screener API can also be hosted via `deploy/screener/`.

### What this does *not* claim
ML potentials can be wrong on exotic organometallics, charged species, and transition states — every score carries provenance and an uncertainty tag. Volatility, shelf life, cost, and safety need chemical knowledge beyond atomistic energies; the tool flags `unknown` rather than inventing numbers. A good screen's job is to know what it does not know and say so.
