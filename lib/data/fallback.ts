import type { Candidate } from "../types";
import { aldPrecursor } from "./ald";

// Resilient offline candidate set — the high-κ gate-dielectric shortlist from
// the design, in the exact post-MP Candidate shape. Served verbatim when
// MP_API_KEY is missing or the API is unreachable, so the demo never fails.
// ehull is in meV/atom; kappa is the total dielectric constant.
type Seed = Omit<Candidate, "ald" | "score">;

const SEED: Seed[] = [
  { id: "mp-352", formula: "HfO2", sys: "Monoclinic", spg: "P2₁/c (14)", eform: -3.95, eg: 5.74, ehull: 0, K: 201, kappa: 25, nsites: 12, density: 9.68 },
  { id: "mp-2858", formula: "ZrO2", sys: "Monoclinic", spg: "P2₁/c (14)", eform: -3.81, eg: 5.42, ehull: 0, K: 187, kappa: 23, nsites: 12, density: 5.83 },
  { id: "mp-2292", formula: "La2O3", sys: "Trigonal", spg: "P-3m1 (164)", eform: -3.74, eg: 5.34, ehull: 0, K: 132, kappa: 27, nsites: 5, density: 6.51 },
  { id: "mp-1539", formula: "Ta2O5", sys: "Orthorhombic", spg: "Pmmm (47)", eform: -3.28, eg: 4.02, ehull: 4, K: 158, kappa: 26, nsites: 14, density: 8.2 },
  { id: "mp-2657", formula: "TiO2", sys: "Tetragonal", spg: "P4₂/mnm (136)", eform: -3.33, eg: 3.26, ehull: 0, K: 210, kappa: 89, nsites: 6, density: 4.25 },
  { id: "mp-1143", formula: "Al2O3", sys: "Trigonal", spg: "R-3c (167)", eform: -3.44, eg: 8.81, ehull: 0, K: 251, kappa: 9.3, nsites: 10, density: 3.99 },
  { id: "mp-2652", formula: "Y2O3", sys: "Cubic", spg: "Ia-3 (206)", eform: -3.82, eg: 4.54, ehull: 0, K: 149, kappa: 14, nsites: 40, density: 5.03 },
  { id: "mp-5229", formula: "SrTiO3", sys: "Cubic", spg: "Pm-3m (221)", eform: -3.55, eg: 3.25, ehull: 0, K: 178, kappa: 300, nsites: 5, density: 5.12 },
  { id: "mp-4991", formula: "HfSiO4", sys: "Tetragonal", spg: "I4₁/amd (141)", eform: -3.61, eg: 6.51, ehull: 7, K: 220, kappa: 11, nsites: 12, density: 6.97 },
  { id: "mp-7000", formula: "SiO2", sys: "Trigonal", spg: "P3₂21 (154)", eform: -3.46, eg: 5.92, ehull: 0, K: 38, kappa: 4.2, nsites: 9, density: 2.65 },
  { id: "mp-989", formula: "Si3N4", sys: "Hexagonal", spg: "P6₃/m (176)", eform: -1.71, eg: 4.46, ehull: 0, K: 230, kappa: 7.5, nsites: 14, density: 3.19 },
  { id: "mp-2605", formula: "Gd2O3", sys: "Cubic", spg: "Ia-3 (206)", eform: -3.78, eg: 4.3, ehull: 0, K: 130, kappa: 16, nsites: 40, density: 7.41 },
];

export const FALLBACK_CANDIDATES: Candidate[] = SEED.map((s) => ({
  ...s,
  ald: aldPrecursor(s.formula),
  score: 0,
}));
