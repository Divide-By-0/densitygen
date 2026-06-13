import type { Candidate, MPStructure } from "../types";
import { aldPrecursor } from "../data/ald";

// Defensive accessors — the MP API returns nulls for sparse properties
// (bulk_modulus, e_total), so we tolerate missing fields rather than throw.
const num = (v: unknown): number | null =>
  typeof v === "number" && Number.isFinite(v) ? v : null;

interface RawSymmetry {
  crystal_system?: string;
  symbol?: string;
  number?: number;
}

/** Map a raw MP summary document into a (pre-scoring) Candidate. */
export function parseSummaryDoc(doc: Record<string, unknown>): Candidate {
  const sym = (doc.symmetry as RawSymmetry) ?? {};
  const bm = doc.bulk_modulus as { vrh?: number } | null;
  const formula = String(doc.formula_pretty ?? "—");
  const ehull = num(doc.energy_above_hull);
  const kappa = num(doc.e_total);

  return {
    id: String(doc.material_id ?? "—"),
    formula,
    sys: sym.crystal_system ?? "—",
    spg: sym.symbol ? `${sym.symbol} (${sym.number ?? "?"})` : "—",
    eform: num(doc.formation_energy_per_atom) ?? 0,
    eg: num(doc.band_gap) ?? 0,
    ehull: ehull == null ? 0 : Math.round(ehull * 1000),
    K: bm?.vrh != null ? Math.round(bm.vrh) : null,
    kappa: kappa == null ? null : Math.round(kappa * 10) / 10,
    nsites: num(doc.nsites) ?? 0,
    density: num(doc.density) ?? 0,
    ald: aldPrecursor(formula),
    score: 0,
    structure: doc.structure ? parseStructure(doc.structure) : undefined,
  };
}

interface RawStructure {
  lattice?: {
    matrix?: number[][];
    a?: number;
    b?: number;
    c?: number;
    alpha?: number;
    beta?: number;
    gamma?: number;
  };
  sites?: Array<{
    species?: Array<{ element?: string }>;
    xyz?: number[];
  }>;
}

export function parseStructure(raw: unknown): MPStructure | undefined {
  const s = raw as RawStructure;
  const lat = s?.lattice;
  if (!lat?.matrix || !s.sites) return undefined;
  return {
    matrix: lat.matrix as [number[], number[], number[]],
    a: lat.a ?? 0,
    b: lat.b ?? 0,
    c: lat.c ?? 0,
    alpha: lat.alpha ?? 90,
    beta: lat.beta ?? 90,
    gamma: lat.gamma ?? 90,
    sites: s.sites
      .filter((st) => st.species?.[0]?.element && st.xyz)
      .map((st) => ({
        element: st.species![0].element!,
        xyz: st.xyz as [number, number, number],
      })),
  };
}
