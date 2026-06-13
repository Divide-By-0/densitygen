// ALD half-reaction systems for the surface-chemistry viewer.
// Authored (illustrative) trajectories + MLIP-style predicted energetics —
// honest about being schematic, not DFT-relaxed coordinates.
export interface SurfaceSystem {
  pre: string; // precursor
  prod: string; // surface product fragment
  by: string; // byproduct
  sym: string; // metal symbol
  color: string; // metal atom color (hex)
  mr: number; // metal sphere radius
  prodF: string; // film formula
  Ea: number; // activation barrier (eV)
  dE: number; // reaction energy (eV)
  kappa: string;
  eg: string;
  temp: string; // ALD window °C
}

export const SURFACE_SYSTEMS: SurfaceSystem[] = [
  { pre: "Al(CH₃)₃", prod: "Al(CH₃)₂", by: "CH₄↑", sym: "Al", color: "#5E83A6", mr: 0.58, prodF: "Al₂O₃", Ea: 0.74, dE: -1.6, kappa: "9.3", eg: "8.8", temp: "150–300" },
  { pre: "Hf[N(CH₃)₂]₄", prod: "Hf(NMe₂)₃", by: "HN(CH₃)₂↑", sym: "Hf", color: "#B45309", mr: 0.66, prodF: "HfO₂", Ea: 0.62, dE: -2.1, kappa: "25", eg: "5.7", temp: "200–350" },
  { pre: "Zr[NMeEt]₄", prod: "Zr(NR₂)₃", by: "HNMeEt↑", sym: "Zr", color: "#C98A3E", mr: 0.64, prodF: "ZrO₂", Ea: 0.68, dE: -1.9, kappa: "23", eg: "5.4", temp: "200–300" },
  { pre: "TiCl₄", prod: "TiCl₃", by: "HCl↑", sym: "Ti", color: "#7C92A6", mr: 0.6, prodF: "TiO₂", Ea: 0.51, dE: -2.4, kappa: "89", eg: "3.3", temp: "150–250" },
];
