import Link from "next/link";
import { getCandidates } from "@/lib/mp/queries";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { CandidatesTable } from "@/components/screens/CandidatesTable";
import { sub, fmtKappa } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function CandidatesPage() {
  const { candidates, source } = await getCandidates();
  const inSpec = candidates.filter((c) => c.inSpec);
  const withK = candidates.filter((c) => c.kappa != null);
  const topK = withK.reduce((m, c) => (c.kappa! > (m.kappa ?? -1) ? c : m), withK[0]);
  const widest = candidates.reduce((m, c) => (c.eg > m.eg ? c : m), candidates[0]);

  return (
    <div className="px-[22px] pb-10 pt-5">
      <ScreenHeader
        eyebrow="02 · Ranked candidates"
        title="High-κ dielectric"
        accent="candidates"
        subtitle={
          <>
            {candidates.length} oxides {source === "live" ? "from Materials Project" : "(cached set)"}, ranked
            by composite score across κ, E_g, stability and K.{" "}
            <span className="mono text-amber-deep">PF</span> = on Pareto front.
          </>
        }
        actions={
          <>
            <Link href="/trade-offs" className="btn-ghost">
              View trade-offs ↗
            </Link>
            <Link href="/compute" className="btn-primary">
              Dispatch top 12 →
            </Link>
          </>
        }
      />

      {/* KPI tiles */}
      <div className="mb-[18px] grid grid-cols-2 gap-px overflow-hidden rounded-[2px] border border-hair bg-hair md:grid-cols-4">
        <Kpi label="Pass spec" value={`${inSpec.length}`} sub={`/ ${candidates.length}`} barW="25%" />
        <Kpi label="Top κ in window" value={fmtKappa(topK?.kappa ?? null)} sub={topK ? sub(topK.formula) : ""} barW="60%" />
        <Kpi label="Widest gap" value={widest.eg.toFixed(2)} sub={`eV ${sub(widest.formula)}`} barW="90%" />
        <Kpi label="Compute used" value="184K" sub="core·hr" barW="37%" />
      </div>

      <CandidatesTable rows={candidates} />

      <div className="mono mt-[11px] flex flex-wrap gap-[18px] text-[11px] text-faint">
        <span>
          <span className="mr-1.5 inline-block h-[7px] w-[7px] rounded-full" style={{ background: "var(--color-ok)" }} />
          passes constraint
        </span>
        <span>κ·E_g·H = κ≥20 · E_g≥5 · e_hull≤25</span>
        <span>missing value → em-dash, never zero</span>
        <span className="ml-auto">click a row → material detail</span>
      </div>
    </div>
  );
}

function Kpi({ label, value, sub, barW }: { label: string; value: string; sub: string; barW: string }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}
        <span className="text-[13px] text-faint"> {sub}</span>
      </div>
      <div className="kpi-bar" style={{ width: barW }} />
    </div>
  );
}
