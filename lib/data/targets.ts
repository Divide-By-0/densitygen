// DFT-queryable property targets the agent translated the fab spec into.
export interface TargetRow {
  p: string;
  op: string;
  tgt: string;
  why: string;
  m: string;
}

export const TARGETS: TargetRow[] = [
  { p: "Dielectric constant κ", op: "≥", tgt: "20", why: "EOT scaling / drive current", m: "DFPT (ε∞ + ionic)" },
  { p: "Band gap E_g", op: "≥", tgt: "5.0 eV", why: "suppress gate leakage", m: "HSE06 (PBE underestimates)" },
  { p: "Energy above hull", op: "≤", tgt: "25 meV/atom", why: "phase stability at anneal", m: "r²SCAN convex hull" },
  { p: "CB offset to Si", op: "≥", tgt: "1.0 eV", why: "electron barrier height", m: "band alignment" },
  { p: "Bulk modulus K", op: "≥", tgt: "130 GPa", why: "mechanical integrity", m: "elastic tensor" },
  { p: "Thermal stability", op: "pass", tgt: "1300 K", why: "anneal survivability", m: "phonon / Gibbs" },
];

export interface ConstraintChip {
  text: string;
  kind: "danger" | "neutral" | "amber";
}

export const HARD_CONSTRAINTS: ConstraintChip[] = [
  { text: "exclude Pb, Cd, Hg, Be, Tl, As", kind: "danger" },
  { text: "exclude radioactive", kind: "danger" },
  { text: "n_elements ≤ 4", kind: "neutral" },
  { text: "ALD precursor exists", kind: "neutral" },
  { text: "BEOL ≤ 450 °C", kind: "neutral" },
  { text: "Si-compatible interface", kind: "amber" },
];
