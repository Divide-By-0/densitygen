"use client";

import { useState } from "react";

type Kind = "ok" | "info" | "warn" | "alert";
const LOG: { t: string; k: Kind; x: string }[] = [
  { t: "14:02:11", k: "ok", x: "Parsed process spec → 6 DFT-queryable targets" },
  { t: "14:02:30", k: "info", x: "MP query: binary/ternary oxides w/ dielectric data (pymatgen)" },
  { t: "14:03:04", k: "info", x: "Filter E_g ≥ 5 ∧ e_hull ≤ 25 → shortlist" },
  { t: "14:03:19", k: "info", x: "Composite rank (κ·E_g·stability·K) → top 12" },
  { t: "14:05:48", k: "ok", x: "Dispatched 12 relaxations · atomate2 → SLURM@perlmutter" },
  { t: "14:09:02", k: "warn", x: "La₂O₃ SCF oscillation — custodian: ALGO=All, AMIX=0.1" },
  { t: "14:11:37", k: "warn", x: "SrTiO₃ pruned-grid risk — set PREC=Accurate" },
  { t: "14:12:10", k: "warn", x: "PBE gap underestimate — queued HSE06 for top 3" },
  { t: "14:14:55", k: "ok", x: "ALD precursor check: HfO₂, ZrO₂ ✓ (TEMAHf/TDMAZr)" },
  { t: "14:15:41", k: "alert", x: "Ta₂O₅ relax not converged (200 ionic) — requeued" },
];

const dotColor: Record<Kind, string> = {
  ok: "var(--color-ok)",
  warn: "var(--color-warn)",
  alert: "var(--color-danger)",
  info: "var(--color-faint)",
};
const txColor: Record<Kind, string> = {
  ok: "var(--color-ink2)",
  warn: "var(--color-amber-deep)",
  alert: "var(--color-danger)",
  info: "var(--color-ink2)",
};

export function AgentTrace() {
  const [open, setOpen] = useState(true);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="Show agent trace"
        className="hidden flex-shrink-0 basis-[34px] cursor-pointer flex-col items-center gap-2 border-l border-hair bg-surface pt-3 lg:flex"
      >
        <span className="dot-blink" />
        <span className="mono text-[9px] tracking-[0.1em] text-faint [writing-mode:vertical-rl]">
          AGENT TRACE
        </span>
      </button>
    );
  }

  return (
    <aside className="hidden min-h-0 flex-shrink-0 basis-[300px] flex-col border-l border-hair bg-surface lg:flex">
      <div className="flex flex-shrink-0 items-center justify-between border-b border-hair px-[14px] py-[11px]">
        <div className="flex items-center gap-2">
          <span className="dot-blink" />
          <span className="text-[13px] font-semibold text-ink">Agent trace</span>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="mono cursor-pointer text-[10px] text-faint hover:text-ink2"
        >
          BACKGROUND ✕
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-auto py-1.5">
        {LOG.map((l, i) => (
          <div key={i} className="flex gap-[9px] border-b border-[#F5F4F1] px-[14px] py-2">
            <span
              className="mt-[5px] h-[7px] w-[7px] flex-shrink-0 rounded-full"
              style={{ background: dotColor[l.k] }}
            />
            <div className="min-w-0">
              <div className="mono text-[10px] text-faint">{l.t}</div>
              <div className="mt-px text-[12px] leading-snug" style={{ color: txColor[l.k] }}>
                {l.x}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex-shrink-0 border-t border-hair bg-canvas px-3 py-2.5">
        <div className="flex items-center gap-2 rounded-[2px] border border-line bg-surface px-[9px] py-[7px]">
          <input
            placeholder="Refine — e.g. exclude rare-earths"
            className="flex-1 bg-transparent text-[12px] text-ink2 outline-none"
          />
          <span className="mono cursor-pointer text-[11px] text-amber">↑</span>
        </div>
        <div className="mono mt-[7px] text-[9.5px] tracking-[0.04em] text-faint">
          DENSITYGEN ENGINE · atomate2 · pymatgen · custodian
        </div>
      </div>
    </aside>
  );
}
