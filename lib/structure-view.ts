import type { MPStructure } from "./types";

// Pure, client-safe projection of a real MP crystal structure into a 2D
// ball-and-stick scene for the SVG viewer (no MP / server imports here).

const ANIONS = new Set(["O", "N", "F", "S", "Cl", "Se", "Br"]);

export interface ProjAtom {
  el: string;
  x: number;
  y: number;
  depth: number;
  r: number;
  anion: boolean;
}
export interface ProjBond {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  depth: number;
}

export interface Scene {
  atoms: ProjAtom[];
  bonds: ProjBond[];
}

/** Build a 1.6× supercell-free projection of the unit cell at the given rotation. */
export function projectStructure(
  structure: MPStructure,
  rotX: number,
  rotY: number,
  size: number,
): Scene {
  const sites = structure.sites;
  if (!sites.length) return { atoms: [], bonds: [] };

  // center
  const c = [0, 0, 0];
  sites.forEach((s) => {
    c[0] += s.xyz[0];
    c[1] += s.xyz[1];
    c[2] += s.xyz[2];
  });
  c[0] /= sites.length;
  c[1] /= sites.length;
  c[2] /= sites.length;

  const cx = Math.cos(rotX),
    sx = Math.sin(rotX),
    cy = Math.cos(rotY),
    sy = Math.sin(rotY);

  const rotated = sites.map((s) => {
    const x = s.xyz[0] - c[0];
    const y = s.xyz[1] - c[1];
    const z = s.xyz[2] - c[2];
    // rotate Y then X
    const x1 = x * cy + z * sy;
    const z1 = -x * sy + z * cy;
    const y1 = y * cx - z1 * sx;
    const z2 = y * sx + z1 * cx;
    return { el: s.element, x: x1, y: y1, z: z2, raw: s.xyz };
  });

  // scale to fit
  let maxR = 0.0001;
  rotated.forEach((p) => {
    maxR = Math.max(maxR, Math.abs(p.x), Math.abs(p.y));
  });
  const scale = (size / 2 - 26) / maxR;
  const cxp = size / 2;
  const cyp = size / 2;

  const atoms: ProjAtom[] = rotated.map((p) => {
    const anion = ANIONS.has(p.el);
    return {
      el: p.el,
      x: cxp + p.x * scale,
      y: cyp - p.y * scale,
      depth: p.z,
      r: anion ? 8.5 : 14,
      anion,
    };
  });

  // bonds: cation–anion pairs within 2.8 Å (real cartesian distance)
  const bonds: ProjBond[] = [];
  for (let i = 0; i < sites.length; i++) {
    for (let j = i + 1; j < sites.length; j++) {
      const a = ANIONS.has(sites[i].element);
      const b = ANIONS.has(sites[j].element);
      if (a === b) continue; // need one cation + one anion
      const d = dist(sites[i].xyz, sites[j].xyz);
      if (d < 2.8) {
        bonds.push({
          x1: atoms[i].x,
          y1: atoms[i].y,
          x2: atoms[j].x,
          y2: atoms[j].y,
          depth: (atoms[i].depth + atoms[j].depth) / 2,
        });
      }
    }
  }

  atoms.sort((p, q) => p.depth - q.depth);
  return { atoms, bonds };
}

function dist(a: number[], b: number[]) {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}

export const isAnion = (el: string) => ANIONS.has(el);
