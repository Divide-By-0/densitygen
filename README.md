# DensityGen: ALD Precursor Screening Platform

## TL;DR Plan

Build DensityGen as a private, hackathon-scope screening platform for ALD precursor discovery. The first version should take candidate precursor molecules plus target film context, run fast ML atomistic estimates instead of first-principles DFT by default, score each candidate against ALD viability constraints, and expose results through a small hosted API on Replicate. Implementation is intentionally gated: this repo currently contains only the plan and README, and no pipeline code should be added until approved.

The intended MVP has four layers:

1. Candidate input: precursor structures, target film, target surface, process temperature window, and optional known hazards.
2. ML compute: use open atomistic models such as FAIR-Chem UMA / OMat24 for inorganic materials and OMol25-derived molecular models for precursor chemistry.
3. Screening logic: rank volatility, thermal stability, adsorption/reactivity, ligand removal risk, carbon contamination risk, byproduct etching risk, and low-temperature process compatibility.
4. Output and tooling: visual report for humans, JSON for automation, and a future CLI/MCP-style tool that Claude Code or similar agents can call.

## Motivation

The film is the working part of the chip. Silicon is the canvas; deposited films insulate, conduct, or block. A modern chip is a stack of hundreds of atom-thin functional layers, and ALD is used because advanced node structures need films that are only a few atoms thick, conformal over 3D geometry, and uniform across dense features.

The precursor is not the product. It is the delivery vehicle that is consumed so the desired solid film can grow one self-limited atomic layer at a time.

| Film | Common precursor examples | Function | Where in the chip |
| --- | --- | --- | --- |
| TiN | TDMAT, TiCl4 | Diffusion barrier / metal-gate electrode | Barrier liners, gate stacks |
| Al2O3 | TMA + H2O | Dielectric / passivation | DRAM, encapsulation |
| HfO2 | TEMAH or HfCl4 + H2O/O3 | High-k gate dielectric | Logic transistor gate |
| W | WF6 + SiH4/B2H6 | Low-resistance fill | Contacts, vias, wordlines |
| Ru, Mo | Organometallics | Liner / interconnect metal | Advanced interconnects |

## Why This Is Hard

A viable ALD precursor has to satisfy a narrow window all at once:

- Volatile enough to deliver as vapor without decomposing.
- Reactive enough to chemisorb on the target surface.
- Self-limiting enough that growth stops after one layer.
- Clean enough that ligands leave completely, especially carbon-containing ligands.
- Active at low temperature, often around 300-400 C or below for advanced integration.
- Safe byproducts that do not etch the growing film or adjacent layers.
- Practical purity, cost, shelf life, and safety.

That intersection is small. The goal is not to replace expert judgment with a lookup table; it is to make the expensive candidate triage loop much faster.

## Product Goal

Create a precursor screening platform that starts with the best available ML atomistic models and only escalates to expensive DFT or experiments for the most promising candidates.

The platform should answer:

- What film are we trying to print?
- Which precursor candidates can deliver the target atoms?
- Which surfaces and co-reactants matter?
- Which candidates are likely volatile, stable, reactive, self-limiting, and clean?
- What evidence supports each score?
- Which next computation or experiment should be run?

## Proposed Architecture

```text
candidate set
  -> structure normalization
  -> property estimation
  -> surface/reaction probes
  -> ALD viability scoring
  -> ranked report + structured JSON
  -> visualization + agent-callable API
```

### Inputs

- Target film: `TiN`, `Al2O3`, `HfO2`, `W`, `Ru`, `Mo`, or a new formula.
- Candidate precursor: SMILES, XYZ, SDF, CIF, or named known precursor.
- Co-reactant: H2O, O3, NH3, plasma, H2, SiH4, B2H6, or custom.
- Target surface: idealized slab, known material, or imported structure.
- Process constraints: temperature ceiling, allowed elements, forbidden ligands, hazard filters.

### ML Compute Layer

Candidate model families to evaluate during implementation:

- FAIR-Chem UMA for broad atomistic energy/force estimation across molecules, materials, catalysts, and surfaces.
- OMat24-trained models for inorganic materials and surface/bulk relaxation tasks.
- OMol25-trained models for molecular precursor energetics, conformers, charges/spins, and reactive geometries.
- Optional fallback baselines: xTB, RDKit descriptors, and cheap DFT for calibration checks.

The first implementation should treat these as scoring engines, not as unquestioned truth. Every score should carry provenance, uncertainty flags, and a suggested validation step.

### Screening Scores

The platform should produce an interpretable scorecard:

- `delivery_score`: volatility proxy, molecular weight, coordination saturation, decomposition risk.
- `surface_reactivity_score`: adsorption energy, ligand exchange plausibility, surface binding motif.
- `self_limiting_score`: steric saturation, reactive site exhaustion, second-layer growth risk.
- `clean_ligand_score`: ligand elimination routes, C/N/H/Cl/F residue risk.
- `thermal_window_score`: predicted stability and reaction feasibility under the temperature cap.
- `byproduct_score`: byproduct volatility and etching/corrosion risk.
- `integration_score`: target film compatibility, forbidden elements, safety and handling notes.

### Deployment Path

Start with Replicate because it gives a simple hosted prediction API and can package arbitrary Python inference code through Cog. The planned serving shape is:

- `predict(input_json) -> ranked_candidates_json`
- optional artifact outputs: CSV, HTML report, molecule/surface images, and trajectory files.
- secrets loaded from environment variables only, never committed.

The user mentioned an API key in `.zshrc`; implementation should read it from the local environment when needed, but this planning repo must not inspect or copy secrets.

### Visualization

Integrate the existing Opus-built visualization pipeline after the first scoring API works. The visualization should make tradeoffs obvious:

- ranked candidate table
- score radar / bar chart
- reaction path snapshots
- surface adsorption geometry
- uncertainty and validation flags
- exportable report for chemists/process engineers

### Future Agent Tool

Expose a stable automation interface after the MVP:

- CLI command such as `ald-screen run candidates.csv --film HfO2 --surface gate_stack.json`.
- JSON schema for requests and responses.
- MCP-style tool wrapper so Claude Code or another coding agent can submit screening jobs, inspect results, and propose next experiments.

## Initial Milestones

1. Repo setup and planning: private GitHub repo, README, plan, collaborator access.
2. Design approval: confirm scope, model choices, and MVP output format.
3. Skeleton only: Python package layout, Cog/Replicate entrypoint, config schema, no scientific claims yet.
4. Local dry run: deterministic mock scorer with sample TiN/Al2O3/HfO2 candidates.
5. Real model spike: run one FAIR-Chem/UMA calculation locally or in a container.
6. Hosted API: deploy first Replicate endpoint with a constrained input schema.
7. Visualization bridge: connect scoring JSON to the Opus visualization pipeline.
8. Validation loop: compare ML scores against known precursor examples and mark failure modes.

## Approval Gate

No implementation should start until this plan is reviewed and approved. The first approved coding task should be narrowly scoped to repo skeleton, dependency strategy, and one mocked end-to-end request.

## References To Verify During Implementation

- FAIR-Chem documentation: https://fair-chem.github.io/
- FAIR-Chem GitHub: https://github.com/facebookresearch/fairchem
- OMat24 paper: https://arxiv.org/abs/2410.12771
- OMol25 paper: https://arxiv.org/abs/2505.08762
- UMA model page: https://huggingface.co/facebook/UMA
- Replicate custom model docs: https://replicate.com/docs/get-started/deploy-a-custom-model
- Cog GitHub: https://github.com/replicate/cog
