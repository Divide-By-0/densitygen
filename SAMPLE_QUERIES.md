# Sample Queries for Chemists

These are the questions ALD and surface-chemistry teams actually ask — the ones
that historically meant queuing a DFT job on a supercomputer for hours-to-days
per candidate, or running a months-long trial-and-error campaign in the lab.
Universal ML interatomic potentials (UMA / MACE / Orb-class models) collapse the
per-candidate atomistic cost from hours of DFT to seconds on one GPU, which is
what makes *screening hundreds of precursors* newly possible.

Each query notes: (1) what the chemist wants, (2) why it was expensive before,
(3) which UMA task head answers it, and (4) how to ask DensityGen.

---

## A. Precursor prioritization (the core loop)

### 1. "I need a new precursor for film X. Which candidates should I pursue first?"
- **Was expensive because:** every candidate needed DFT for adsorption + a lab
  trial for volatility/thermal window. You could only afford to try a handful.
- **Model:** `oc20` (adsorption), `omol` (stability), descriptors (volatility).
- **Ask:**
  ```bash
  ald-screen run examples/new_material_screen.json
  ```
  Returns a ranked scorecard across delivery / thermal window / surface
  reactivity / self-limiting / clean-ligand / byproduct / integration.

### 2. "Tungsten fill: is there anything better than WF6 that avoids HF?"
- **Why it matters:** WF6 works but its HF byproduct etches the oxide/Si it sits
  on — a genuine integration headache. Chlorides, carbonyls, organometallics?
- **Ask:** `ald-screen run examples/wf6_w.json` — DensityGen ranks WF6 #1 but
  flags `byproduct=0.45 (HF etches oxides/Si)`; WCl6/WCl5 trade HF for HCl and a
  volatility penalty; W(CO)6 avoids halogens entirely. The scorecard makes the
  tradeoff explicit instead of hidden in tribal knowledge.

### 3. "Rank these 200 candidate molecules for HfO2 by ALD viability."
- **Was expensive because:** 200 DFT relaxations + adsorption calcs = weeks of
  cluster time. UMA does 200 single-points in minutes.
- **Ask:** a single request with 200 candidates; results sorted, with a
  `recommended_next_step` per candidate so you know which 5 deserve real DFT.

---

## B. Surface chemistry — does it stick, and does it stop?

### 4. "Will this precursor chemisorb on a hydroxylated HfO2/SiO2 surface, or just physisorb?"
- **Was expensive because:** adsorption energy on a realistic slab is a full DFT
  surface calculation (large supercell, k-points) — hours each.
- **Model:** `oc20` adsorption energy = E(slab+ads) − E(slab) − E(gas). Negative
  and large ⇒ chemisorption ⇒ good ALD. Near zero ⇒ won't nucleate.
- **Ask:** set `use_ml_potential: true` and supply the slab + adsorbate
  structures; the `surface_reactivity` component flips from `~estimated` to
  `✓measured` with the actual UMA energy.

### 5. "Is the surface reaction self-limiting, or will it run away into CVD?"
- **The unknown:** steric saturation of the surface after one ligand exchange —
  the defining property of ALD. Hard to measure directly; needs the saturated
  surface coverage energetics.
- **Model:** `oc20` adsorption energy vs. coverage; second-layer adsorption near
  zero ⇒ self-limiting.

### 6. "Which surface sites does it actually bind — bridging, on-top, oxygen vacancy?"
- **Was expensive because:** an adsorption-site sweep is N separate DFT runs.
  UMA evaluates all candidate sites cheaply, so you map the binding landscape.

### 7. "How does growth differ on the first ALD cycle vs. steady state (nucleation delay)?"
- **The unknown:** nucleation delay on a foreign starting surface (e.g. W on a
  TiN liner) wastes cycles and roughens films. Needs first-cycle vs. bulk-cycle
  energetics on *different* surfaces.

---

## C. Thermal stability & decomposition (clean films)

### 8. "What's the highest temperature I can run before the precursor self-decomposes in the line?"
- **Was expensive because:** decomposition onset is a bond-breaking /
  transition-state question — DFT or careful TGA. For novel ligands there's no
  literature number at all.
- **Model:** `omol` ligand-bond and decomposition-fragment energetics.
- **Ask:** `thermal_window` component; pass `temperature_max_c` to test against
  your thermal budget. (DensityGen already shows the honest tension here: TEMAH,
  which *has* a measured 250 °C onset, scores its thermal window lower than a
  chemically similar amide whose onset is merely *estimated* — a flag that you
  should run UMA to fill the missing decomposition energy rather than trust the
  optimistic default.)

### 9. "Will the ligands leave cleanly, or will I get carbon/chlorine/fluorine residue in the film?"
- **Why it matters:** residual C/Cl/F wrecks k-value, leakage, and resistivity.
- **Model:** `omol` ligand-elimination pathway energetics + the `clean_ligand`
  descriptor (carbon fraction, halogen flags).

### 10. "Are the byproducts benign, or will they etch the film I just grew?"
- **The unknown:** HF (from fluorides) and HCl (from chlorides) re-etch oxides;
  hydrocarbons/amines are benign. Quantifying the etch thermodynamics needs DFT.
- **Model:** `omat`/`omol` byproduct formation + etch energetics; the
  `byproduct` component flags it today from chemistry rules.

---

## D. Materials discovery & "what if" (the supercomputer questions)

### 11. "Is this brand-new film even thermodynamically stable to deposit by ALD?"
- **Model:** `omat` bulk/surface formation energy. Cheap convex-hull-style
  stability screening that used to be a DFT high-throughput project.

### 12. "We want to move from W to Mo to cut line resistance — which Mo precursor family wins?"
- **Ask:** `ald-screen run examples/new_material_screen.json` — screens
  MoF6 / MoCl5 / MoO2Cl2 / Mo(CO)6 / Mo(NMe2)4 / MoCp2 in one shot and tells you
  which to take to DFT/lab. This is a genuine industry direction (Mo/Ru
  interconnects at advanced nodes).

### 13. "Design a ligand shell that maximizes volatility while staying carbon-clean."
- **The unknown:** inverse design — search ligand space for the volatility /
  cleanliness / stability Pareto front. UMA makes the objective evaluations cheap
  enough to put a search loop around.

### 14. "Given my forbidden-element list (no Cl in this module), what's my best option?"
- **Ask:** `forbidden_elements: ["Cl"]` — see `examples/hfo2_highk.json`, where
  the gate correctly demotes HfCl4 below halide-free amides despite HfCl4 being
  the most thermally robust.

---

## E. Process integration

### 15. "Does my co-reactant choice (H2O vs O3 vs plasma) change which precursor wins?"
- Re-run the same candidates with different `co_reactant`; aggressiveness feeds
  the surface-reactivity and byproduct components.

### 16. "This precursor is great on paper but is it pyrophoric/toxic? What's the handling risk?"
- Hazard flags from the curated DB surface in `warnings` (e.g. TMA pyrophoric,
  WF6 toxic/corrosive) so safety enters the ranking conversation early.

---

## How the model maps to the question

| Question type | UMA task head | What it returns |
|---|---|---|
| Does it stick / self-limit? | `oc20` | adsorption energy on a slab (eV) |
| Is it stable / clean? | `omol` | molecular & ligand-fragment energies |
| Is the film/byproduct favorable? | `omat` | bulk/surface formation energy |
| Fast pre-filter (no GPU) | — | volatility/residue descriptors |

The discipline: **descriptors triage for free, UMA confirms the survivors, DFT
adjudicates the final few.** DensityGen's `recommended_next_step` enforces that
escalation ladder per candidate so you never spend supercomputer time on a
precursor that a 1-second check already ruled out.
