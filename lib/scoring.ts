import type { Candidate } from "./types";

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/**
 * Composite fit score for a high-κ gate-dielectric search.
 * Weighted blend of dielectric constant, band gap, phase stability and
 * mechanical integrity — the four axes the design's run-plan ranks on.
 * Missing κ / K fall back to a neutral 0.5 so a material isn't unfairly buried.
 */
export function compositeScore(c: Candidate): number {
  const kTerm = c.kappa == null ? 0.5 : clamp01(Math.log10(c.kappa) / Math.log10(60));
  const egTerm = clamp01(c.eg / 9);
  const stabTerm = clamp01(1 - c.ehull / 50);
  const modTerm = c.K == null ? 0.5 : clamp01(c.K / 250);
  const s = 0.34 * kTerm + 0.3 * egTerm + 0.21 * stabTerm + 0.15 * modTerm;
  return Math.round(s * 100);
}

/**
 * Annotate candidates in place: pass flags, κ×E_g Pareto dominance,
 * composite score and rank. Returns a new sorted-by-score array.
 */
export function scoreCandidates(rows: Candidate[]): Candidate[] {
  const scored = rows.map((r) => ({
    ...r,
    passK: r.kappa != null && r.kappa >= 20,
    passEg: r.eg >= 5,
    passHull: r.ehull <= 25,
    score: compositeScore(r),
  }));

  scored.forEach((r) => {
    r.inSpec = !!(r.passK && r.passEg && r.passHull);
  });

  // Pareto dominance — maximise κ and E_g (only κ-bearing points compete).
  scored.forEach((a) => {
    if (a.kappa == null) {
      a.front = false;
      return;
    }
    a.front = !scored.some(
      (b) =>
        b !== a &&
        b.kappa != null &&
        b.kappa >= a.kappa! &&
        b.eg >= a.eg &&
        (b.kappa > a.kappa! || b.eg > a.eg),
    );
  });

  const byScore = [...scored].sort((x, y) => y.score - x.score);
  byScore.forEach((r, i) => {
    r.rank = i + 1;
  });
  return byScore;
}

export const passColor = (ehull: number) =>
  ehull === 0 ? "var(--color-ok)" : ehull <= 25 ? "var(--color-warn)" : "var(--color-danger)";
