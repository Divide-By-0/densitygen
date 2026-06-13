const SUBS = "₀₁₂₃₄₅₆₇₈₉";

/** Convert ASCII digits in a chemical formula to unicode subscripts. */
export function sub(formula: string): string {
  return formula.replace(/[0-9]/g, (d) => SUBS[+d]);
}

/** Format energy-above-hull (meV) — "0" when stable, never a bare zero loss. */
export const fmtHull = (mev: number) => (mev === 0 ? "0" : String(mev));

export const fmtKappa = (k: number | null) =>
  k == null ? "—" : k >= 100 ? String(Math.round(k)) : k.toFixed(1);
