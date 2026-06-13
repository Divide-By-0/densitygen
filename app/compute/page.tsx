import { JOBS, JOB_STATUS_STYLE } from "@/lib/data/jobs";

export default function ComputePage() {
  const n = (s: string) => JOBS.filter((j) => j.st === s).length;
  const counts = [
    { label: "Converged", v: n("converged"), c: "var(--color-ok)" },
    { label: "Running", v: n("running"), c: "var(--color-amber-deep)" },
    { label: "Queued", v: n("queued"), c: "var(--color-muted)" },
    { label: "Flagged", v: n("flagged"), c: "var(--color-warn)" },
    { label: "Failed", v: n("failed"), c: "var(--color-danger)" },
  ];

  return (
    <div className="px-[22px] pb-10 pt-5">
      <div className="eyebrow">04 · Compute dispatch</div>
      <div className="my-1 flex flex-wrap items-end justify-between gap-x-5 gap-y-3.5">
        <div className="min-w-[290px] flex-1 basis-[360px]">
          <h1 className="display text-[32px]">
            Live DFT <span className="accent">dispatch</span>
          </h1>
          <p className="mt-1 text-[13px] text-muted">
            atomate2 workflows on <span className="mono text-ink2">SLURM@nersc-perlmutter</span> · custodian
            auto-handles SCF / convergence failures.
          </p>
        </div>
        <div className="mono flex items-center gap-2 text-[11px] text-muted">
          <span className="dot-blink" />
          {n("running")} RUNNING
        </div>
      </div>

      <div className="mb-[18px] grid grid-cols-2 gap-px overflow-hidden rounded-[2px] border border-hair bg-hair sm:grid-cols-3 md:grid-cols-5">
        {counts.map((c) => (
          <div key={c.label} className="bg-surface px-3.5 py-3">
            <div className="mono text-[10px] uppercase tracking-[0.06em] text-faint">{c.label}</div>
            <div className="mono mt-1.5 text-[23px] font-semibold" style={{ color: c.c }}>
              {c.v}
            </div>
          </div>
        ))}
      </div>

      <div className="overflow-auto rounded-[2px] border border-hair bg-surface">
        <table className="dg-table min-w-[1000px]">
          <thead>
            <tr>
              <th className="!text-left">Task</th>
              <th className="!text-left">Material</th>
              <th className="!text-left">Calc</th>
              <th className="!text-left">Functional</th>
              <th className="!text-left">k-mesh</th>
              <th className="!text-right">SCF</th>
              <th className="!text-right">ΔE</th>
              <th className="!text-right">Wall</th>
              <th className="!text-left" style={{ width: 220 }}>
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {JOBS.map((j) => {
              const s = JOB_STATUS_STYLE[j.st];
              const barColor =
                j.st === "failed" ? "var(--color-danger)" : j.st === "converged" ? "var(--color-ok)" : "var(--color-amber)";
              return (
                <tr key={j.id}>
                  <td className="mono text-[11.5px] text-muted">{j.id}</td>
                  <td className="font-semibold text-ink">{j.f}</td>
                  <td className="text-ink2">{j.calc}</td>
                  <td className="mono text-ink2">{j.func}</td>
                  <td className="mono text-[11px] text-muted">{j.k}</td>
                  <td className="mono !text-right text-muted">{j.scf}</td>
                  <td className="mono !text-right text-muted">{j.de}</td>
                  <td className="mono !text-right text-muted">{j.wall}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <span
                        className="mono whitespace-nowrap rounded-[2px] border px-[7px] py-[3px] text-[10px] tracking-[0.04em]"
                        style={{ color: s.c, background: s.bg, borderColor: s.br }}
                      >
                        {j.st.toUpperCase()}
                      </span>
                      <div className="h-[5px] min-w-[40px] flex-1 overflow-hidden rounded-[2px] bg-hair2">
                        <div className="h-full" style={{ width: `${j.prog}%`, background: barColor }} />
                      </div>
                    </div>
                    {j.warn && (
                      <div className="mono mt-1.5 text-[10.5px] leading-snug text-amber-deep">⚠ {j.warn}</div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mono mt-[11px] text-[11.5px] text-faint">
        custodian intercepts SCF oscillation, ionic non-convergence and grid-sensitivity warnings — the
        craft that usually costs hours of manual restarts.
      </p>
    </div>
  );
}
