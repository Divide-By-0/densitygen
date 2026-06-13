// Periodic-table layout for the chemical-search-space panel.
// cat: h=focus · o=oxide-former · t=anion(O) · x=excluded · n=default
export type ElemCat = "h" | "o" | "t" | "x" | "n";
export interface Elem {
  sym: string;
  col: number;
  row: number; // 1–7 main block, 8–9 f-block
  cat: ElemCat;
}

const RAW =
  "H,1,1,n He,18,1,n Li,1,2,n Be,2,2,x B,13,2,n C,14,2,n N,15,2,o O,16,2,t F,17,2,n Ne,18,2,n Na,1,3,n Mg,2,3,o Al,13,3,o Si,14,3,o P,15,3,n S,16,3,n Cl,17,3,n Ar,18,3,n K,1,4,n Ca,2,4,o Sc,3,4,o Ti,4,4,o V,5,4,n Cr,6,4,n Mn,7,4,n Fe,8,4,n Co,9,4,n Ni,10,4,n Cu,11,4,n Zn,12,4,n Ga,13,4,o Ge,14,4,o As,15,4,x Se,16,4,n Br,17,4,n Kr,18,4,n Rb,1,5,n Sr,2,5,o Y,3,5,o Zr,4,5,o Nb,5,5,o Mo,6,5,n Tc,7,5,x Ru,8,5,n Rh,9,5,n Pd,10,5,n Ag,11,5,n Cd,12,5,x In,13,5,n Sn,14,5,o Sb,15,5,n Te,16,5,n I,17,5,n Xe,18,5,n Cs,1,6,n Ba,2,6,o La,3,6,o Hf,4,6,h Ta,5,6,o W,6,6,n Re,7,6,n Os,8,6,n Ir,9,6,n Pt,10,6,n Au,11,6,n Hg,12,6,x Tl,13,6,x Pb,14,6,x Bi,15,6,n Po,16,6,x At,17,6,x Rn,18,6,x Fr,1,7,x Ra,2,7,x Ac,3,7,x Rf,4,7,n Db,5,7,n Sg,6,7,n Bh,7,7,n Hs,8,7,n Mt,9,7,n Ds,10,7,n Rg,11,7,n Cn,12,7,n Nh,13,7,n Fl,14,7,n Mc,15,7,n Lv,16,7,n Ts,17,7,n Og,18,7,n Ce,4,8,o Pr,5,8,o Nd,6,8,o Pm,7,8,x Sm,8,8,o Eu,9,8,o Gd,10,8,o Tb,11,8,o Dy,12,8,o Ho,13,8,o Er,14,8,o Tm,15,8,o Yb,16,8,o Lu,17,8,o Th,4,9,x Pa,5,9,x U,6,9,x Np,7,9,x Pu,8,9,x Am,9,9,x Cm,10,9,x Bk,11,9,x Cf,12,9,x Es,13,9,n Fm,14,9,n Md,15,9,n No,16,9,n Lr,17,9,n";

const ALL: Elem[] = RAW.trim()
  .split(/\s+/)
  .map((s) => {
    const [sym, col, row, cat] = s.split(",");
    return { sym, col: +col, row: +row, cat: cat as ElemCat };
  });

export const PT_MAIN = ALL.filter((e) => e.row <= 7);
export const PT_F = ALL.filter((e) => e.row >= 8).map((e) => ({ ...e, row: e.row - 7 }));

export const CAT_CLASS: Record<ElemCat, string> = {
  h: "bg-amber text-white border-amber-deep",
  o: "bg-amber-tint text-amber-deep border-amber-border",
  t: "bg-ink text-white border-ink",
  x: "bg-danger-tint text-danger border-danger-border",
  n: "bg-canvas text-faint border-hair2",
};
