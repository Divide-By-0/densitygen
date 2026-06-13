import { getCandidates } from "@/lib/mp/queries";

export async function RunContextStrip() {
  const { total, candidates, source } = await getCandidates();
  const inSpec = candidates.filter((c) => c.inSpec).length;
  const top = Math.min(12, candidates.length);

  return (
    <div className="flex h-10 flex-shrink-0 items-stretch overflow-hidden border-b border-hair bg-surface text-[12px]">
      <Cell label="PROJECT">
        <span className="font-medium text-ink">High-κ gate dielectric · GAA CMOS</span>
      </Cell>
      <Cell label="SPEC" className="hidden md:flex">
        <span className="mono text-ink2">κ≥20 · E_g≥5eV · e_hull≤25 · CMOS · ALD</span>
      </Cell>
      <Cell label="METHOD" className="hidden lg:flex">
        <span className="text-ink2">r²SCAN → HSE06</span>
      </Cell>
      <div className="ml-auto flex items-center gap-3 px-4">
        <span
          className="mono flex items-center gap-1.5 text-[10px] tracking-[0.06em]"
          style={{ color: source === "live" ? "var(--color-ok)" : "var(--color-warn)" }}
        >
          <span
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={{ background: source === "live" ? "var(--color-ok)" : "var(--color-warn)" }}
          />
          {source === "live" ? "LIVE · MATERIALS PROJECT" : "CACHED"}
        </span>
        <span className="mono font-medium text-amber-deep">
          {total.toLocaleString()} → {inSpec} → {top}
        </span>
      </div>
    </div>
  );
}

function Cell({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2 border-r border-hair px-4 ${className}`}>
      <span className="mono text-[10px] tracking-[0.1em] text-faint">{label}</span>
      {children}
    </div>
  );
}
