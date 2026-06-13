// Curated ALD/CVD precursor knowledge — NOT in Materials Project.
// Maps a material's cation chemistry to the precursor(s) actually used to
// deposit it, in rough priority order (the metal that defines the film).

const PRECURSORS: Array<[string, string]> = [
  ["Hf", "TEMAHf / TDMAHf"],
  ["Zr", "TEMAZr / ZrCl₄"],
  ["Ta", "TaCl₅ / PDMAT"],
  ["Nb", "Nb(OEt)₅ / NbCl₅"],
  ["Ti", "TiCl₄ / TDMAT"],
  ["La", "La(thd)₃"],
  ["Y", "Y(thd)₃ / Y(Cp)₃"],
  ["Sc", "Sc(thd)₃"],
  ["Gd", "Gd(thd)₃"],
  ["Sr", "Sr(thd)₂"],
  ["Ba", "Ba(thd)₂"],
  ["Al", "TMA / H₂O"],
  ["Si", "BDEAS / O₃"],
  ["Mg", "Mg(Cp)₂ / H₂O"],
  ["Ga", "TMGa / H₂O"],
  ["W", "WF₆ / WCl₅"],
  ["Mo", "MoO₂Cl₂ / Mo(CO)₆"],
];

/** Extract element symbols from a pretty formula like "Sr2Ta2O7". */
export function elementsOf(formula: string): string[] {
  return Array.from(formula.matchAll(/[A-Z][a-z]?/g)).map((m) => m[0]);
}

export function aldPrecursor(formula: string): string {
  const els = new Set(elementsOf(formula));
  for (const [el, pre] of PRECURSORS) {
    if (els.has(el)) return pre;
  }
  return "—";
}
