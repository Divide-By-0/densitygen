// HER (hydrogen evolution) Sabatier volcano — ΔG_H* vs exchange-current
// activity. Curated literature values; the apex sits at ΔG_H* ≈ 0.
export type CatClass = "precious" | "base" | "target";

export interface Catalyst {
  sym: string;
  g: number; // ΔG_H* (eV)
  a: number; // activity, log10(i0)
  cls: CatClass;
  lab: boolean; // show label
}

export const CATALYSTS: Catalyst[] = [
  { sym: "Pt", g: 0.0, a: -0.04, cls: "precious", lab: true },
  { sym: "Ir", g: -0.05, a: -0.1, cls: "precious", lab: false },
  { sym: "Pd", g: -0.2, a: -0.3, cls: "precious", lab: true },
  { sym: "Rh", g: -0.27, a: -0.4, cls: "precious", lab: false },
  { sym: "Re", g: -0.45, a: -0.78, cls: "precious", lab: false },
  { sym: "Ni", g: -0.32, a: -0.5, cls: "base", lab: true },
  { sym: "Co", g: -0.28, a: -0.44, cls: "base", lab: false },
  { sym: "Cu", g: 0.22, a: -0.42, cls: "base", lab: true },
  { sym: "Au", g: 0.3, a: -0.58, cls: "precious", lab: true },
  { sym: "Ag", g: 0.45, a: -0.82, cls: "precious", lab: true },
  { sym: "Mo", g: -0.55, a: -0.9, cls: "base", lab: true },
  { sym: "W", g: -0.5, a: -0.84, cls: "base", lab: true },
  { sym: "Nb", g: -0.62, a: -0.98, cls: "base", lab: false },
  { sym: "MoS₂", g: 0.09, a: -0.16, cls: "target", lab: true },
  { sym: "Ni₂P", g: 0.13, a: -0.22, cls: "target", lab: true },
  { sym: "CoP", g: 0.17, a: -0.3, cls: "target", lab: false },
];
