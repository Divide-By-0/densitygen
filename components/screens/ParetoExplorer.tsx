"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Candidate } from "@/lib/types";
import { sub, fmtKappa, fmtHull } from "@/lib/format";
import { CATALYSTS } from "@/lib/data/volcano";

type Variant = "scatter" | "volcano" | "tradeoff";

// plot area within the 880×500 viewBox
const X0 = 78,
  X1 = 836,
  Y0 = 28,
  Y1 = 452;

export function ParetoExplorer({ candidates }: { candidates: Candidate[] }) {
  const router = useRouter();
  const pts = useMemo(() => candidates.filter((c) => c.kappa != null), [candidates]);
  const kMax = useMemo(() => Math.max(400, ...pts.map((c) => c.kappa!)), [pts]);
  const egMax = useMemo(
    () => Math.max(9.5, Math.ceil(Math.max(...candidates.map((c) => c.eg)))),
    [candidates],
  );

  const [variant, setVariant] = useState<Variant>("scatter");
  const [selId, setSel] = useState<string>(() => pts.find((p) => p.front)?.id ?? pts[0]?.id);
  const [hoverId, setHover] = useState<string | null>(null);

  const pxK = (k: number) =>
    X0 + ((Math.log10(k) - Math.log10(3)) / (Math.log10(kMax) - Math.log10(3))) * (X1 - X0);
  const pyE = (e: number) => Y1 - (e / egMax) * (Y1 - Y0);

  // fall back to the full candidate set (not just κ-bearing points) so the
  // readout never dereferences undefined when no candidate has dielectric data
  const sel = candidates.find((c) => c.id === selId) ?? candidates[0];
  const inSpec = candidates.filter((c) => c.inSpec).length;

  const frontPts = pts
    .filter((p) => p.front)
    .sort((a, b) => a.kappa! - b.kappa!);
  const frontPoly = frontPts.map((p) => `${pxK(p.kappa!).toFixed(1)},${pyE(p.eg).toFixed(1)}`).join(" ");

  const kTicks = [3, 10, 30, 100, 300, 1000].filter((k) => k <= kMax);
  const egTicks = Array.from({ length: Math.floor(egMax / 2) + 1 }, (_, i) => i * 2);

  return (
    <div className="px-[22px] pb-10 pt-5">
      <div className="eyebrow">03 · Trade-off explorer</div>
      <div className="my-1 flex flex-wrap items-end justify-between gap-x-5 gap-y-3.5">
        <div className="min-w-[290px] flex-1 basis-[360px]">
          <h1 className="display text-[32px]">
            Property <span className="accent">trade-offs</span>
          </h1>
          <p className="mt-1 text-[13px] text-muted">
            No single material maximises every target — explore the frontier where gains in one property
            cost another. Live Materials Project κ and E_g.
          </p>
        </div>
        <div className="inline-flex flex-shrink-0 overflow-hidden rounded-[2px] border border-line">
          <Seg on={variant === "scatter"} onClick={() => setVariant("scatter")}>
            κ × E_g Pareto
          </Seg>
          <Seg on={variant === "volcano"} onClick={() => setVariant("volcano")}>
            ΔE_ads volcano
          </Seg>
          <Seg on={variant === "tradeoff"} onClick={() => setVariant("tradeoff")} last>
            Constraint explorer
          </Seg>
        </div>
      </div>

      {variant === "scatter" && (
        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1fr_270px]">
          <div className="relative rounded-[2px] border border-hair bg-surface p-2 pb-1">
            <div className="flex justify-between px-2 pb-0.5 pt-1.5">
              <span className="mono text-[11px] text-muted">DIELECTRICS · κ vs E_g · maximise both ↗</span>
              <span className="mono text-[11px] text-amber-deep">VARIANT A</span>
            </div>
            <svg viewBox="0 0 880 500" className="block h-auto w-full">
              <rect x={X0} y={Y0} width={X1 - X0} height={Y1 - Y0} fill="var(--color-canvas)" />
              {/* target window κ≥20 ∧ E_g≥5 */}
              <rect
                x={pxK(20)}
                y={pyE(egMax)}
                width={X1 - pxK(20)}
                height={pyE(5) - pyE(egMax)}
                fill="var(--color-amber-tint)"
                stroke="var(--color-amber)"
                strokeWidth={1}
                strokeDasharray="4 3"
                opacity={0.7}
              />
              <text x={pxK(20)} y={44} dx={8} fill="var(--color-amber-deep)" className="mono" fontSize={11}>
                TARGET WINDOW · κ≥20 ∧ E_g≥5
              </text>
              {egTicks.map((t) => (
                <g key={t}>
                  <line x1={X0} y1={pyE(t)} x2={X1} y2={pyE(t)} stroke="#EFEDE8" strokeWidth={1} />
                  <text x={70} y={pyE(t)} dy={3} fill="var(--color-faint)" className="mono" fontSize={10} textAnchor="end">
                    {t}
                  </text>
                </g>
              ))}
              {kTicks.map((t) => (
                <text key={t} x={pxK(t)} y={468} fill="var(--color-faint)" className="mono" fontSize={10} textAnchor="middle">
                  {t}
                </text>
              ))}
              <polyline points={frontPoly} fill="none" stroke="var(--color-amber)" strokeWidth={1.6} strokeDasharray="5 3" />
              {pts.map((p) => {
                const x = pxK(p.kappa!);
                const y = pyE(p.eg);
                const isSel = p.id === selId;
                return (
                  <circle
                    key={p.id}
                    cx={x}
                    cy={y}
                    r={isSel ? 9 : p.front ? 7 : 5.5}
                    fill={p.front ? "var(--color-amber)" : "#FFFFFF"}
                    stroke={isSel ? "var(--color-ink)" : p.front ? "var(--color-amber-deep)" : "var(--color-line)"}
                    strokeWidth={isSel ? 2.5 : 1.4}
                    opacity={p.front ? 1 : 0.9}
                    style={{ cursor: "pointer" }}
                    onClick={() => setSel(p.id)}
                    onMouseEnter={() => setHover(p.id)}
                    onMouseLeave={() => setHover(null)}
                  />
                );
              })}
              {frontPts.map((p) => (
                <text
                  key={p.id}
                  x={pxK(p.kappa!) + 11}
                  y={pyE(p.eg) - 9}
                  fill="var(--color-amber-deep)"
                  className="mono"
                  fontSize={11}
                  fontWeight={500}
                >
                  {sub(p.formula)}
                </text>
              ))}
              <text x={457} y={492} fill="var(--color-muted)" fontSize={12} textAnchor="middle">
                Dielectric constant κ (log scale)
              </text>
              <text x={22} y={240} fill="var(--color-muted)" fontSize={12} textAnchor="middle" transform="rotate(-90 22 240)">
                Band gap E_g (eV, HSE06)
              </text>
            </svg>
            {hoverId && <HoverCard c={candidates.find((c) => c.id === hoverId)!} px={pxK} py={pyE} />}
          </div>

          {/* readout */}
          <div className="rounded-[2px] border border-hair bg-surface">
            <div className="flex items-center justify-between border-b border-hair px-[13px] py-[11px]">
              <span className="text-[13px] font-semibold text-ink">{sub(sel.formula)}</span>
              <span className="mono text-[11px] text-muted">{sel.id}</span>
            </div>
            <div className="p-[13px]">
              <Row k="Dielectric κ" v={fmtKappa(sel.kappa)} />
              <Row k="Band gap E_g" v={`${sel.eg.toFixed(2)} eV`} />
              <Row k="e above hull" v={`${fmtHull(sel.ehull)} meV`} />
              <Row k="Bulk modulus K" v={`${sel.K ?? "—"} GPa`} last />
              <button onClick={() => router.push(`/material/${sel.id}`)} className="btn-primary mt-3 w-full">
                Open material detail →
              </button>
            </div>
            <div className="border-t border-hair bg-canvas px-[13px] py-[11px]">
              <div className="mono mb-1.5 text-[10px] uppercase tracking-[0.08em] text-faint">Reading the frontier</div>
              <p className="text-[11.5px] leading-relaxed text-muted">
                Amber points are Pareto-optimal — no material beats them on both κ and E_g. Hollow points are
                dominated. The shaded box is your spec window.
              </p>
            </div>
          </div>
        </div>
      )}

      {variant === "volcano" && <Volcano />}
      {variant === "tradeoff" && (
        <ConstraintExplorer pts={pts} pxK={pxK} pyE={pyE} kMax={kMax} egMax={egMax} inSpec={inSpec} total={candidates.length} />
      )}
    </div>
  );
}

function HoverCard({
  c,
  px,
  py,
}: {
  c: Candidate;
  px: (k: number) => number;
  py: (e: number) => number;
}) {
  return (
    <div
      className="mono pointer-events-none absolute z-10 whitespace-nowrap rounded-[2px] bg-ink px-[9px] py-[7px] text-[11px] text-[#EDEBE6] shadow-lg"
      style={{ left: `${(px(c.kappa!) / 880) * 100}%`, top: `${(py(c.eg) / 500) * 100}%` }}
    >
      <b className="text-white">{sub(c.formula)}</b> · {c.id}
      <br />κ {fmtKappa(c.kappa)} · E_g {c.eg.toFixed(2)} eV · hull {fmtHull(c.ehull)}
      <br />
      <span style={{ color: "#E6A463" }}>{c.front ? "Pareto-optimal" : "dominated"}</span>
    </div>
  );
}

function Volcano() {
  const pxG = (g: number) => X0 + ((g + 0.7) / 1.3) * (X1 - X0);
  const pyA = (a: number) => Y0 + ((0.05 - a) / 1.1) * (Y1 - Y0);
  let vc = "";
  for (let g = -0.7; g <= 0.6001; g += 0.02) {
    const a = -0.02 - 0.92 * Math.abs(g);
    vc += `${pxG(g).toFixed(1)},${pyA(a).toFixed(1)} `;
  }
  return (
    <div className="rounded-[2px] border border-hair bg-surface p-2 pb-1">
      <div className="flex justify-between px-2 pb-0.5 pt-1.5">
        <span className="mono text-[11px] text-muted">HER CATALYSTS · activity vs ΔG_H* · Sabatier volcano</span>
        <span className="mono text-[11px] text-amber-deep">VARIANT B</span>
      </div>
      <svg viewBox="0 0 880 500" className="block h-auto w-full">
        <rect x={X0} y={Y0} width={X1 - X0} height={Y1 - Y0} fill="var(--color-canvas)" />
        {[0, -0.3, -0.6, -0.9].map((a) => (
          <g key={a}>
            <line x1={X0} y1={pyA(a)} x2={X1} y2={pyA(a)} stroke="#EFEDE8" strokeWidth={1} />
            <text x={70} y={pyA(a)} dy={3} fill="var(--color-faint)" className="mono" fontSize={10} textAnchor="end">
              {a.toFixed(1)}
            </text>
          </g>
        ))}
        {[-0.6, -0.4, -0.2, 0, 0.2, 0.4].map((g) => (
          <text key={g} x={pxG(g)} y={468} fill="var(--color-faint)" className="mono" fontSize={10} textAnchor="middle">
            {g.toFixed(1)}
          </text>
        ))}
        <line x1={pxG(0)} y1={Y0} x2={pxG(0)} y2={Y1} stroke="var(--color-amber)" strokeWidth={1} strokeDasharray="4 3" opacity={0.6} />
        <text x={pxG(0)} y={42} fill="var(--color-amber-deep)" className="mono" fontSize={11} textAnchor="middle">
          ΔG_H* ≈ 0 · optimum
        </text>
        <polyline points={vc.trim()} fill="none" stroke="#C9C6C0" strokeWidth={1.6} />
        {CATALYSTS.map((c) => {
          const x = pxG(c.g);
          const y = pyA(c.a);
          const target = c.cls === "target";
          const precious = c.cls === "precious";
          return (
            <g key={c.sym}>
              <circle
                cx={x}
                cy={y}
                r={target ? 7 : 5.5}
                fill={target ? "var(--color-amber)" : precious ? "#FFFFFF" : "var(--color-ink2)"}
                stroke={target ? "var(--color-amber-deep)" : precious ? "#334155" : "var(--color-ink2)"}
                strokeWidth={precious ? 1.6 : 1.2}
              />
              {c.lab && (
                <text x={x} y={y - 11} fill={target ? "var(--color-amber-deep)" : "var(--color-muted)"} className="mono" fontSize={11} textAnchor="middle">
                  {c.sym}
                </text>
              )}
            </g>
          );
        })}
        <text x={457} y={492} fill="var(--color-muted)" fontSize={12} textAnchor="middle">
          Hydrogen adsorption free energy ΔG_H* (eV)
        </text>
        <text x={22} y={240} fill="var(--color-muted)" fontSize={12} textAnchor="middle" transform="rotate(-90 22 240)">
          Activity log₁₀(i₀)
        </text>
      </svg>
      <div className="mono flex flex-wrap gap-5 px-3 pb-2 pt-1.5 text-[11px] text-muted">
        <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-amber" />earth-abundant target</span>
        <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-ink2" />base metal</span>
        <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full border-[1.5px] border-[#334155]" />precious metal</span>
        <span className="ml-auto text-amber-deep">MoS₂ / Ni₂P sit near the apex at a fraction of Pt cost</span>
      </div>
    </div>
  );
}

function ConstraintExplorer({
  pts,
  pxK,
  pyE,
  kMax,
  egMax,
  inSpec,
  total,
}: {
  pts: Candidate[];
  pxK: (k: number) => number;
  pyE: (e: number) => number;
  kMax: number;
  egMax: number;
  inSpec: number;
  total: number;
}) {
  const nb = 8;
  const lo = Math.log10(3),
    hi = Math.log10(kMax);
  const histK = Array.from({ length: nb }, (_, b) =>
    pts.filter((p) => {
      const l = Math.log10(p.kappa!);
      return l >= lo + ((hi - lo) * b) / nb && l < lo + ((hi - lo) * (b + 1)) / nb;
    }).length,
  );
  const maxK = Math.max(...histK, 1);
  const histE = Array.from({ length: nb }, (_, b) =>
    pts.filter((p) => p.eg >= (egMax * b) / nb && p.eg < (egMax * (b + 1)) / nb).length,
  );
  const maxE = Math.max(...histE, 1);

  return (
    <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1fr_230px]">
      <div className="rounded-[2px] border border-hair bg-surface p-2 pb-1">
        <div className="flex justify-between px-2 pb-0.5 pt-1.5">
          <span className="mono text-[11px] text-muted">CONSTRAINT EXPLORER · marginal distributions + live window</span>
          <span className="mono text-[11px] text-amber-deep">VARIANT C</span>
        </div>
        {/* top marginal: kappa histogram */}
        <div className="mb-0.5 flex h-[46px] items-end gap-[3px] pl-[78px] pr-2">
          {histK.map((c, b) => (
            <div
              key={b}
              className="min-h-[2px] flex-1 rounded-t-[1px]"
              style={{ height: `${(c / maxK) * 100}%`, background: b / nb >= (Math.log10(20) - lo) / (hi - lo) ? "var(--color-amber)" : "var(--color-hair)" }}
            />
          ))}
        </div>
        <svg viewBox="0 0 880 470" className="block h-auto w-full">
          <rect x={X0} y={10} width={X1 - X0} height={412} fill="var(--color-canvas)" />
          <rect x={pxK(20)} y={10} width={X1 - pxK(20)} height={pyE(5) - 10} fill="var(--color-amber-tint)" opacity={0.6} />
          <line x1={pxK(20)} y1={10} x2={pxK(20)} y2={422} stroke="var(--color-amber)" strokeWidth={1.4} strokeDasharray="5 3" />
          <line x1={X0} y1={pyE(5)} x2={X1} y2={pyE(5)} stroke="var(--color-amber)" strokeWidth={1.4} strokeDasharray="5 3" />
          <text x={pxK(20)} y={416} dx={5} fill="var(--color-amber-deep)" className="mono" fontSize={10}>κ = 20</text>
          <text x={82} y={pyE(5)} dy={-4} fill="var(--color-amber-deep)" className="mono" fontSize={10}>E_g = 5.0 eV</text>
          {pts.map((p) => (
            <circle
              key={p.id}
              cx={pxK(p.kappa!)}
              cy={pyE(p.eg)}
              r={p.front ? 7 : 5.5}
              fill={p.front ? "var(--color-amber)" : "#FFFFFF"}
              stroke={p.front ? "var(--color-amber-deep)" : "var(--color-line)"}
              strokeWidth={1.4}
              opacity={0.9}
            />
          ))}
          <text x={457} y={448} fill="var(--color-muted)" fontSize={12} textAnchor="middle">
            Dielectric constant κ (log scale)
          </text>
        </svg>
      </div>
      <div className="flex flex-col gap-3">
        <div className="rounded-[2px] border border-hair bg-surface p-[13px]">
          <div className="mono text-[10px] uppercase tracking-[0.08em] text-faint">In spec window</div>
          <div className="mono mt-1.5 text-[30px] font-semibold text-ink">
            {inSpec}
            <span className="text-[15px] text-faint"> / {total}</span>
          </div>
          <div className="mt-2.5 h-[2px] bg-amber" style={{ width: "25%" }} />
        </div>
        <div className="rounded-[2px] border border-hair bg-surface p-[13px]">
          <div className="mono mb-2 text-[10px] uppercase tracking-[0.08em] text-faint">E_g distribution →</div>
          {histE
            .map((c, b) => ({ c, b }))
            .reverse()
            .map(({ c, b }) => (
              <div key={b} className="mb-[3px] flex items-center gap-1.5">
                <div className="h-2 min-w-[2px] rounded-[1px] bg-line" style={{ width: `${(c / maxE) * 100}%` }} />
                <span className="mono text-[10px] text-faint">{c}</span>
              </div>
            ))}
        </div>
        <div className="rounded-[2px] border border-hair bg-canvas px-[13px] py-[11px]">
          <p className="text-[11.5px] leading-relaxed text-muted">
            Constraint lines mark κ≥20 and E_g≥5. Histograms show how few candidates clear each axis — the
            joint window is the scarce upper-right quadrant.
          </p>
        </div>
      </div>
    </div>
  );
}

function Seg({ on, onClick, children, last }: { on: boolean; onClick: () => void; children: React.ReactNode; last?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`cursor-pointer px-3.5 py-2 text-[12px] font-medium ${last ? "" : "border-r border-hair"}`}
      style={{ background: on ? "var(--color-amber-tint)" : "#fff", color: on ? "var(--color-amber-deep)" : "var(--color-muted)" }}
    >
      {children}
    </button>
  );
}

function Row({ k, v, last }: { k: string; v: string; last?: boolean }) {
  return (
    <div className={`flex justify-between py-[5px] ${last ? "" : "border-b border-hair2"}`}>
      <span className="text-[12px] text-muted">{k}</span>
      <span className="mono font-medium text-ink">{v}</span>
    </div>
  );
}
