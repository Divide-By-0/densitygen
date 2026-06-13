import { cache } from "react";
import { mpFetch } from "./client";
import { parseSummaryDoc } from "./schemas";
import { scoreCandidates } from "../scoring";
import { FALLBACK_CANDIDATES } from "../data/fallback";
import type { Candidate, CandidateResult, MPStructure } from "../types";

const SUMMARY_FIELDS =
  "material_id,formula_pretty,nelements,nsites,density,symmetry,band_gap,formation_energy_per_atom,energy_above_hull,bulk_modulus,e_total";

/**
 * The hero query: stable oxides that carry real dielectric data, ranked by
 * total dielectric constant κ (e_total). This surfaces genuine high-κ
 * candidates — and the real κ–E_g anticorrelation — from Materials Project.
 * Falls back to the bundled set if the key is missing or MP is unreachable.
 */
export const getCandidates = cache(async (): Promise<CandidateResult> => {
  try {
    const json = await mpFetch("/materials/summary/", {
      _fields: SUMMARY_FIELDS,
      elements: "O",
      nelements_max: 3,
      has_props: "dielectric",
      band_gap_min: 1.5,
      energy_above_hull_max: 0.08,
      // exclude toxics + non-oxide formers → clean metal-oxide dielectrics
      exclude_elements: "Pb,Cd,Hg,Be,Tl,As,H,C,N,F,Cl,S,P,Se,Br,I",
      _sort_fields: "-e_total",
      _limit: 60,
    });
    const rows = json.data.map(parseSummaryDoc);
    // An empty live result is as unusable as an error — fall back rather than
    // ship a candidate-less app (which would crash the Material screen).
    if (rows.length === 0) throw new Error("MP returned no candidates");
    const candidates = scoreCandidates(rows);
    return {
      candidates,
      source: "live",
      total: json.meta.total_doc,
      note: `MP query → ${json.meta.total_doc} dielectric oxides · top ${candidates.length} ranked`,
    };
  } catch {
    return {
      candidates: scoreCandidates(FALLBACK_CANDIDATES),
      source: "cached",
      total: FALLBACK_CANDIDATES.length,
      note: "MP unavailable — served cached candidate set",
    };
  }
});

/** Fetch a single material's relaxed structure for the crystal viewer. */
export const getMaterialStructure = cache(
  async (id: string): Promise<MPStructure | undefined> => {
    try {
      const json = await mpFetch("/materials/summary/", {
        _fields: "material_id,structure",
        material_ids: id,
        _limit: 1,
      });
      const doc = json.data?.[0];
      return doc ? parseSummaryDoc(doc).structure : undefined;
    } catch {
      return undefined;
    }
  },
);

/** Resolve a candidate by id from the scored set (for the detail screen). */
export async function getCandidateById(
  id: string,
): Promise<{ candidate: Candidate; structure?: MPStructure; source: CandidateResult["source"] }> {
  const { candidates, source } = await getCandidates();
  const candidate = candidates.find((c) => c.id === id) ?? candidates[0];
  const structure = await getMaterialStructure(candidate.id);
  return { candidate, structure, source };
}
