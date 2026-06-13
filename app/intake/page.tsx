import Link from "next/link";
import { TARGETS, HARD_CONSTRAINTS } from "@/lib/data/targets";
import { PT_MAIN, PT_F, CAT_CLASS } from "@/lib/data/periodic";

export default function IntakePage() {
  return (
    <div className="max-w-[1120px] px-[22px] pb-10 pt-5">
      <div className="eyebrow">01 · Process-spec intake</div>
      <h1 className="display mt-1 text-[32px]">
        Translate a fab requirement into <span className="accent">DFT targets</span>
      </h1>
      <p className="mb-[18px] mt-0.5 text-[13px] text-muted">
        densitygen parses an engineering spec into computable property targets, hard constraints, and a
        chemical search space — the judgement-heavy first step of every campaign.
      </p>

      <div className="grid grid-cols-1 items-start gap-[18px] lg:grid-cols-2">
        {/* left column */}
        <div className="flex flex-col gap-4">
          <div className="card">
            <div className="card-head">
              <span>Engineering requirement</span>
              <span className="mono text-[10px] tracking-[0.08em] text-faint">NATURAL LANGUAGE</span>
            </div>
            <div className="serif px-[15px] py-3.5 text-[17px] leading-relaxed text-ink">
              “We need a high-κ gate dielectric for sub-3 nm gate-all-around CMOS to replace the SiO₂/HfO₂
              stack. It must suppress gate leakage, survive the ~1000 °C dopant-activation anneal, deposit
              conformally by ALD on Si, and stay thermodynamically stable through BEOL.”
            </div>
            <div className="flex items-center gap-2 border-t border-hair bg-canvas px-[15px] py-[11px]">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--color-ok)" }} />
              <span className="mono text-[11px]" style={{ color: "var(--color-ok)" }}>
                PARSED
              </span>
              <span className="text-[12px] text-muted">→ 6 targets · 5 constraints · chemical space below</span>
            </div>
          </div>

          <div className="card">
            <div className="card-head">Hard constraints</div>
            <div className="flex flex-wrap gap-[7px] px-[15px] py-3.5">
              {HARD_CONSTRAINTS.map((c) => (
                <span
                  key={c.text}
                  className={
                    c.kind === "danger" ? "tag tag-danger" : c.kind === "amber" ? "tag tag-amber" : "tag"
                  }
                >
                  {c.text}
                </span>
              ))}
            </div>
          </div>

          <div className="card !border-line">
            <div className="card-head">Run plan</div>
            <div className="mono px-[15px] py-3.5 text-[12px] leading-[1.9] text-ink2">
              <div>
                <span className="text-faint">1 ·</span> query Materials Project · dielectric oxides ≤ 3 el →{" "}
                <span className="text-amber-deep">live</span>
              </div>
              <div>
                <span className="text-faint">2 ·</span> filter E_g≥5 ∧ e_hull≤25 → shortlist
              </div>
              <div>
                <span className="text-faint">3 ·</span> composite rank → top <span className="text-amber-deep">12</span>
              </div>
              <div>
                <span className="text-faint">4 ·</span> dispatch r²SCAN relax + DFPT + HSE06
              </div>
            </div>
            <div className="flex gap-2 border-t border-hair px-[15px] py-[11px]">
              <Link href="/candidates" className="btn-primary flex-1 text-center">
                Launch search →
              </Link>
              <button className="btn-ghost">Save spec</button>
            </div>
          </div>
        </div>

        {/* right column */}
        <div className="flex flex-col gap-4">
          <div className="card overflow-hidden">
            <div className="card-head">
              <span>DFT-queryable targets</span>
              <span className="mono text-[10px] text-faint">AGENT-TRANSLATED</span>
            </div>
            <table className="dg-table">
              <thead>
                <tr>
                  <th className="!text-left">Property</th>
                  <th className="!text-left">Target</th>
                  <th className="!text-left">DFT method</th>
                </tr>
              </thead>
              <tbody>
                {TARGETS.map((t) => (
                  <tr key={t.p}>
                    <td>
                      <div className="font-medium text-ink">{t.p}</div>
                      <div className="text-[11px] text-faint">{t.why}</div>
                    </td>
                    <td className="mono whitespace-nowrap text-amber-deep">
                      {t.op} {t.tgt}
                    </td>
                    <td className="text-[11px] text-muted">{t.m}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <div className="card-head">
              <span>Chemical search space</span>
              <span className="mono text-[10px] text-faint">PERIODIC</span>
            </div>
            <div className="p-3.5">
              <PeriodicGrid />
              <div className="mono mt-3 flex flex-wrap gap-3.5 text-[11px] text-muted">
                <Legend swatch="bg-amber" label="focus" />
                <Legend swatch="bg-amber-tint border border-amber-border" label="oxide-former" />
                <Legend swatch="bg-ink" label="anion O" />
                <Legend swatch="bg-danger-tint border border-danger-border" label="excluded" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PeriodicGrid() {
  return (
    <>
      <div className="grid gap-[2px]" style={{ gridTemplateColumns: "repeat(18,1fr)" }}>
        {PT_MAIN.map((e) => (
          <Cell key={`${e.sym}-${e.row}`} e={e} />
        ))}
      </div>
      <div className="mt-[5px] grid gap-[2px]" style={{ gridTemplateColumns: "repeat(18,1fr)" }}>
        {PT_F.map((e) => (
          <Cell key={`${e.sym}-${e.row}`} e={e} />
        ))}
      </div>
    </>
  );
}

function Cell({ e }: { e: (typeof PT_MAIN)[number] }) {
  return (
    <div
      className={`mono flex aspect-square items-center justify-center rounded-[1px] border text-[9px] font-medium ${CAT_CLASS[e.cat]}`}
      style={{ gridColumn: e.col, gridRow: e.row }}
    >
      {e.sym}
    </div>
  );
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span>
      <span className={`mr-1.5 inline-block h-2.5 w-2.5 rounded-[1px] align-[-1px] ${swatch}`} />
      {label}
    </span>
  );
}
