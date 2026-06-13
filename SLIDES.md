# DensityGen — Workflow Slides

A two-slide walkthrough of how the tool works and each step in the process.

---

## Slide 1 — The idea: an escalation ladder

**Problem:** every new chip generation needs a new atom-thin film — and a *precursor* molecule to deposit it by ALD. Finding that precursor today is **months** of trial-and-error and hours-per-candidate of supercomputer DFT.

**DensityGen's move:** triage *everything* cheaply, spend expensive physics only on the finalists.

```
   MANY candidates            A FEW survivors           1–2 finalists
 ┌───────────────────┐      ┌────────────────────┐    ┌────────────────┐
 │  Descriptor        │      │  Real ML potential  │    │  DFT / lab      │
 │  scorecard (7-axis)│ ───▶ │  UMA → CHGNet       │──▶ │  confirmation   │
 │                    │ gates│  omol / oc20 / omat │top │                 │
 │  instant · no GPU  │ drop │  seconds, not hours │ k  │  you decide     │
 └───────────────────┘ fails └────────────────────┘    └────────────────┘
        100s                       ~3–5                      ~1–2
```

- **UMA** = Meta FAIR's universal ML interatomic potential: energies/forces in seconds, replacing hours-to-days of DFT.
- DensityGen is everything *around* UMA: it proposes molecules, builds their structures, scores ALD viability, and decides which calculations are even worth running.

---

## Slide 2 — The pipeline, step by step

```
 ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
 │ 1 INPUT  │─▶│ 2 GET     │─▶│ 3 BUILD   │─▶│ 4 TRIAGE │─▶│ 6 UMA    │─▶│ 7 RANK + │
 │ film +   │  │ candidates│  │ 3D atoms  │  │ 7-axis   │  │ survivors│  │ 8 VIZ +  │
 │ limits   │  │ screen OR │  │ (ASE)     │  │ + 5 gates│  │ (real ML)│  │ 9 SHIP   │
 └──────────┘  │ design    │  └───────────┘  └──────────┘  └──────────┘  └──────────┘
               └───────────┘
```

| # | Step | What happens |
|---|------|--------------|
| 1 | **Input** | Target film (`W`, `HfO2`, `NbP`…) + optional temp ceiling & forbidden elements. **Co-reactant auto-picked** from film kind (oxide→oxidant, nitride→nitridant, metal→reductant). |
| 2 | **Get candidates** | **Screen** = you give a shortlist · **Design** = the inverse-design loop *invents* them (metal + ligand library + mixes). |
| 3 | **Build structures** | ASE turns each name/formula into 3D atoms (UMA relaxes them, so a rough geometry is enough). |
| 4 | **Triage** | Seven-axis scorecard on **every** candidate: delivery, thermal window, surface reactivity, self-limiting, clean-ligand, byproduct, integration. Instant, no GPU. |
| 5 | **Hard gates** | No film element, or a forbidden element → score 0 *before* any expensive compute. |
| 6 | **Escalate** | Top few → real ML potential: **UMA** (gated→Replicate) or **CHGNet** (ungated). Heads: `omol` stability · `oc20` adsorption/self-limiting · `omat` formation. |
| 7 | **Rank + recommend** | Scores carry evidence + confidence (`✓ measured` / `~ estimated`) and a next step (descriptor → UMA → DFT → experiment). |
| 8 | **Visualize** | DataCore dashboard at `/viz`: Pareto trade-off front + 7-axis radar, live "suggest a precursor" re-rank. |
| 9 | **Ship** | CLI `ald-screen`, JSON/CSV, hosted API, deployed web app. |

**Test case it reproduces:** WF₆ → W ranks #1 for tungsten; TMA (no tungsten) hard-fails. The design loop re-derives WF₆ on its own — proof the search is sane.

**One-liners to see it:**
```bash
ald-screen demo                                   # WF6 -> W headline case
ald-screen design --film NbP                      # invent precursors where none exist
ald-screen interconnects                          # screen what has precursors, design what doesn't
```
