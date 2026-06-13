// Shared domain types for densitygen.

export interface MPSite {
  element: string;
  xyz: [number, number, number];
}

export interface MPStructure {
  matrix: [number[], number[], number[]];
  a: number;
  b: number;
  c: number;
  alpha: number;
  beta: number;
  gamma: number;
  sites: MPSite[];
}

/** A scored material candidate (post-MP, post-scoring). */
export interface Candidate {
  id: string; // material_id, e.g. "mp-aaaaaano"
  formula: string; // formula_pretty, e.g. "NaTaO3"
  sys: string; // crystal system
  spg: string; // "P2_1/c (14)"
  eform: number; // formation energy per atom (eV/atom)
  eg: number; // band gap (eV)
  ehull: number; // energy above hull (meV/atom)
  K: number | null; // bulk modulus K_VRH (GPa)
  kappa: number | null; // total dielectric constant (e_total)
  nsites: number;
  density: number; // g/cm^3
  ald: string; // ALD precursor (curated, or "—")
  score: number; // composite fit score 0–100

  // derived by scoring
  rank?: number;
  passK?: boolean;
  passEg?: boolean;
  passHull?: boolean;
  front?: boolean; // on κ×E_g Pareto front
  inSpec?: boolean;

  structure?: MPStructure;
}

export type DataSource = "live" | "cached";

export interface CandidateResult {
  candidates: Candidate[];
  source: DataSource;
  total: number; // total docs matched in MP (or fallback count)
  note: string; // human-readable provenance line for the agent trace
}
