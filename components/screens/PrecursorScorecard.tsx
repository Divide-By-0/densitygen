import type { ScorecardResult } from "@/lib/engine/queries";
import type { Confidence, ScorecardCandidate } from "@/lib/engine/types";
import { SUPPORTED_FILMS } from "@/lib/data/precursors";
import { sub } from "@/lib/format";

const confStyle: Record<Confidence, { c: string; bg: string; br: string }> = {
  measured: { c: "var(--color-ok)", bg: "var(--color-ok-tint)", br: "var(--color-ok-border)" },
  estimated: { c: "var(--color-amber-deep)", bg: "var(--color-amber-tint)", br: "var(--color-amber-border)" },
  unknown: { c: "var(--color-muted)", bg: "var(--color-panel)", br: "var(--color-hair)" },
};
const pct = (s: number) => `${Math.round(s * 100)}%`;

export function PrecursorScorecard({
  result,
  formula,
}: {
  result: ScorecardResult | null;
  formula: string;
}) {
  if (!result) {
    return (
      <div className="card">
        <div className="card-head">
          <span>ALD precursor screening</span>
          <span className="mono text-[10px] text-faint">DENSITYGEN ENGINE</span>
        </div>
        <div className="p-[13px] text-[12.5px] leading-relaxed text-muted">
          No backend ALD recipe maps to <span className="mono text-ink">{sub(formula)}</span> yet. Live
          precursor screening is available for{" "}
          <span className="mono text-amber-deep">{SUPPORTED_FILMS.map(sub).join(", ")}</span> — pick one of
          those candidates to see a real 7-axis viability scorecard.
        </div>
      </div>
    );
  }

  const { response, film, source } = result;
  const ranked = response.ranked_candidates;
  const top = ranked[0];
  const backend = response.model_provenance?.compute_backend ?? "engine";
  const live = source === "live";

  return (
    <div className="card overflow-hidden">
      <div className="card-head">
        <span>
          ALD precursor screening · <span className="mono text-amber-deep">{sub(film)}</span>
        </span>
        <span className="mono flex items-center gap-1.5 text-[10px]" style={{ color: live ? "var(--color-ok)" : "var(--color-warn)" }}>
          <span className="dot-blink" /> {live ? "LIVE ENGINE" : "CACHED ENGINE"} · {backend}
        </span>
      </div>

      {/* ranked precursors */}
      <table className="dg-table">
        <thead>
          <tr>
            <th className="!text-right">#</th>
            <th className="!text-left">Precursor</th>
            <th className="!text-left">Formula</th>
            <th className="!text-right">MW</th>
            <th className="!text-left">Viability</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((r, i) => (
            <tr key={r.name} style={i === 0 ? { background: "var(--color-amber-tint)" } : undefined}>
              <td className="mono !text-right text-faint">{i + 1}</td>
              <td>
                <span className="font-semibold text-ink">{r.name}</span>
                {r.is_known_recipe && (
                  <span className="mono ml-1.5 text-[10px] text-amber-deep" title="known literature recipe">
                    ★
                  </span>
                )}
              </td>
              <td className="mono text-[11.5px] text-muted">{r.formula ? sub(r.formula) : "—"}</td>
              <td className="mono !text-right text-muted">
                {r.molecular_weight ? r.molecular_weight.toFixed(0) : "—"}
              </td>
              <td>
                <div className="flex items-center gap-2">
                  <div className="h-[5px] min-w-[60px] flex-1 overflow-hidden rounded-[2px] bg-hair2">
                    <div className="h-full bg-amber" style={{ width: pct(r.overall_score) }} />
                  </div>
                  <span className="mono text-[11.5px] font-medium text-ink">{pct(r.overall_score)}</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* top candidate 7-axis breakdown */}
      <div className="border-t border-hair p-[13px]">
        <div className="mb-2.5 flex items-baseline justify-between">
          <span className="text-[13px] font-semibold text-ink">
            {top.name} <span className="mono text-[11px] font-normal text-muted">— 7-axis viability</span>
          </span>
          {top.ml_energy_ev != null && (
            <span className="mono text-[11px] text-amber-deep">MLIP E = {top.ml_energy_ev.toFixed(2)} eV</span>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {top.components.map((cmp) => (
            <Axis key={cmp.name} name={cmp.name} score={cmp.score} evidence={cmp.evidence} confidence={cmp.confidence} />
          ))}
        </div>
        <div className="mt-3 rounded-[2px] border border-amber-border bg-amber-tint px-3 py-2.5">
          <div className="mono text-[10px] uppercase tracking-[0.08em] text-amber-deep">Recommended next step</div>
          <div className="mt-1 text-[12px] leading-snug text-ink2">{top.recommended_next_step}</div>
        </div>
      </div>

      {response.model_provenance?.notes && (
        <div className="mono border-t border-hair bg-canvas px-[13px] py-2.5 text-[10px] leading-relaxed text-faint">
          {response.model_provenance.notes}
        </div>
      )}
    </div>
  );
}

function Axis({
  name,
  score,
  evidence,
  confidence,
}: {
  name: string;
  score: number;
  evidence: string;
  confidence: Confidence;
}) {
  const cs = confStyle[confidence] ?? confStyle.unknown;
  return (
    <div className="grid grid-cols-[130px_1fr] items-start gap-3">
      <div className="mono pt-px text-[11px] text-ink2">{name.replace(/_/g, " ")}</div>
      <div>
        <div className="flex items-center gap-2">
          <div className="h-[6px] min-w-[60px] flex-1 overflow-hidden rounded-[2px] bg-hair2">
            <div className="h-full" style={{ width: pct(score), background: score >= 0.66 ? "var(--color-ok)" : score >= 0.4 ? "var(--color-amber)" : "var(--color-danger)" }} />
          </div>
          <span className="mono text-[11px] font-medium text-ink">{pct(score)}</span>
          <span
            className="mono rounded-[2px] border px-1.5 py-px text-[9px]"
            style={{ color: cs.c, background: cs.bg, borderColor: cs.br }}
          >
            {confidence}
          </span>
        </div>
        <div className="mt-1 text-[11px] leading-snug text-muted">{evidence}</div>
      </div>
    </div>
  );
}

export type { ScorecardCandidate };
