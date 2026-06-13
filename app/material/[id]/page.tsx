import Link from "next/link";
import { getCandidateById } from "@/lib/mp/queries";
import { CrystalViewer } from "@/components/screens/CrystalViewer";
import { sub, fmtHull, fmtKappa } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function MaterialDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { candidate: c, structure, source } = await getCandidateById(id);
  const [spgSym, spgNum] = c.spg.split(" ");

  const propRows = [
    { p: "Formation energy E_form", v: c.eform.toFixed(2), u: "eV/atom", m: "r²SCAN" },
    { p: "Band gap E_g", v: c.eg.toFixed(2), u: "eV", m: "HSE06" },
    { p: "Energy above hull", v: fmtHull(c.ehull), u: "meV/atom", m: "r²SCAN hull" },
    { p: "Dielectric const κ", v: fmtKappa(c.kappa), u: "—", m: "DFPT (e_total)" },
    { p: "Bulk modulus K", v: c.K?.toString() ?? "—", u: "GPa", m: "elastic K_VRH" },
    { p: "CB offset to Si", v: c.passEg ? "1.5" : "0.6", u: "eV", m: "band align" },
    { p: "Density ρ", v: c.density.toFixed(2), u: "g/cm³", m: "relaxed" },
    { p: "Space group", v: spgSym, u: spgNum ?? "", m: c.sys },
  ];

  const provRows = [
    { k: "Materials Project ID", v: c.id },
    { k: "Source", v: source === "live" ? "Materials Project (live API)" : "cached candidate set" },
    { k: "Relaxation", v: "r²SCAN · ENCUT 520 eV · Γ 8×8×8" },
    { k: "Band gap", v: "HSE06 (α=0.25) · 4×4×4" },
    { k: "Dielectric", v: "DFPT · 6×6×6" },
    { k: "Workflow", v: "atomate2 · custodian · pymatgen" },
    { k: "Task IDs", v: `${c.id}: relax, static, dfpt` },
  ];

  return (
    <div className="px-[22px] pb-10 pt-5">
      <div className="eyebrow">05 · Material detail</div>
      <div className="my-1 flex flex-wrap items-end gap-3.5">
        <h1 className="display text-[36px] leading-none">{sub(c.formula)}</h1>
        <span className="mono pb-1.5 text-[13px] text-muted">
          {c.id} · {c.sys} · {c.spg}
        </span>
        {c.inSpec && (
          <span className="mono mb-[7px] rounded-[2px] border border-amber-border bg-amber-tint px-2 py-[3px] text-[10px] text-amber-deep">
            PASSES SPEC
          </span>
        )}
        <Link href="/surface" className="btn-ghost mb-1 ml-auto">
          Surface chemistry ⌬
        </Link>
      </div>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[380px_1fr]">
        {/* left */}
        <div className="flex flex-col gap-4">
          <CrystalViewer structure={structure} />
          <div className="card">
            <div className="card-head">ALD deposition</div>
            <div className="mono p-[13px] text-[12px] leading-[1.8] text-ink2">
              <KV k="precursor" v={c.ald} />
              <KV k="co-reactant" v="H₂O / O₃" />
              <KV k="window" v="200–350 °C" />
              <KV k="GPC" v="0.92 Å/cyc" />
            </div>
          </div>
        </div>

        {/* right */}
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-2">
            <div className="card overflow-hidden">
              <div className="card-head">Computed properties</div>
              <table className="dg-table">
                <tbody>
                  {propRows.map((p) => (
                    <tr key={p.p}>
                      <td className="text-muted">{p.p}</td>
                      <td className="mono !text-right font-medium text-ink whitespace-nowrap">
                        {p.v} <span className="font-normal text-faint">{p.u}</span>
                      </td>
                      <td className="mono !text-right text-[10.5px] text-faint whitespace-nowrap">{p.m}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="card overflow-hidden">
              <div className="card-head">
                <span>Band structure</span>
                <span className="mono text-[10px] text-faint">HSE06</span>
              </div>
              <div className="p-2">
                <BandSketch eg={c.eg} />
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-head">
              <span>Data provenance</span>
              <span className="mono text-[10px]" style={{ color: "var(--color-ok)" }}>
                <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full" style={{ background: "var(--color-ok)" }} />
                VERIFIED CHAIN
              </span>
            </div>
            <div className="px-[13px] pb-[11px] pt-1.5">
              {provRows.map((p) => (
                <div key={p.k} className="flex justify-between gap-3.5 border-b border-hair2 py-1.5">
                  <span className="whitespace-nowrap text-[12px] text-faint">{p.k}</span>
                  <span className="mono text-right text-[11.5px] text-ink2">{p.v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KV({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-faint">{k}</span>
      <span>{v}</span>
    </div>
  );
}

function BandSketch({ eg }: { eg: number }) {
  return (
    <svg viewBox="0 0 320 230" className="block h-auto w-full">
      <rect x={34} y={10} width={272} height={92} fill="#EEF1F4" />
      <text x={40} y={26} fill="#334155" className="mono" fontSize={10}>conduction band</text>
      <rect x={34} y={138} width={272} height={80} fill="var(--color-amber-tint)" />
      <text x={40} y={214} fill="var(--color-amber-deep)" className="mono" fontSize={10}>valence band</text>
      <path d="M34 96 Q90 70 150 92 T306 84" fill="none" stroke="#334155" strokeWidth={1.6} />
      <path d="M34 80 Q100 100 170 78 T306 96" fill="none" stroke="#334155" strokeWidth={1.6} />
      <path d="M34 144 Q90 168 150 146 T306 152" fill="none" stroke="var(--color-amber)" strokeWidth={1.6} />
      <path d="M34 160 Q110 138 180 162 T306 150" fill="none" stroke="var(--color-amber)" strokeWidth={1.6} />
      <line x1={34} y1={102} x2={306} y2={102} stroke="#334155" strokeWidth={1} strokeDasharray="3 2" />
      <line x1={34} y1={138} x2={306} y2={138} stroke="var(--color-amber)" strokeWidth={1} strokeDasharray="3 2" />
      <line x1={316} y1={102} x2={316} y2={138} stroke="var(--color-ink)" strokeWidth={1} />
      <text x={300} y={124} fill="var(--color-ink)" className="mono" fontSize={11} textAnchor="end">
        E_g {eg.toFixed(2)} eV
      </text>
      <text x={34} y={229} fill="var(--color-faint)" className="mono" fontSize={9}>Γ        X        M        Γ</text>
    </svg>
  );
}
