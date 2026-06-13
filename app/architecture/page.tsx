import { ENGINE_URL } from "@/lib/engine/client";

export default function ArchitecturePage() {
  return (
    <div className="mx-auto max-w-[1100px] px-[22px] pb-12 pt-5">
      <div className="eyebrow">06 · Architecture</div>
      <h1 className="display mt-1 text-[32px]">
        How it&rsquo;s <span className="accent">built</span>
      </h1>
      <p className="mb-5 mt-1 text-[13px] text-muted">
        Claude builds and deploys the stack; the physics engines compute; the app renders the model output.
        One demo surface — this Vercel app — talking to a live model backend.
      </p>

      {/* ---------- BUILD & DEPLOY ---------- */}
      <SectionLabel n="A" title="Build & deploy — with Claude" />
      <div className="card mb-2 p-4">
        <div className="grid grid-cols-1 items-stretch gap-3 md:grid-cols-[200px_36px_1fr]">
          <Box dark title="Claude · Opus 4.8" sub="Claude Code — writes, reviews, deploys the whole stack">
            <Chip>build</Chip>
            <Chip>review</Chip>
            <Chip>deploy</Chip>
          </Box>
          <Arrow />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Box title="Next.js web app" sub="this UI — screens, scorecards, 3D">
              <Deploy to="Vercel" url="densitygen.vercel.app" />
            </Box>
            <Box title="Screening engine" sub="FastAPI + ALD scorecard + MLIP hook">
              <Deploy to="Hugging Face Space" url={ENGINE_URL.replace(/^https?:\/\//, "")} />
            </Box>
          </div>
        </div>
      </div>

      <FlowArrow label="a user asks for the next material" />

      {/* ---------- RUNTIME ---------- */}
      <SectionLabel n="B" title="Run time — fetch the model output, render it" />

      <div className="card p-4">
        <Lane
          step="INPUT"
          title="Natural-language fab spec"
          body="“a barrierless 2 nm interconnect metal to replace copper”"
          serif
        />
        <Down />
        <div className="rounded-[2px] border border-amber-border bg-amber-tint px-4 py-3">
          <div className="mono text-[11px] tracking-[0.08em] text-amber-deep">OPUS 4.8 · ORCHESTRATION</div>
          <div className="mt-1.5 flex flex-wrap gap-2">
            <Chip>translate spec → targets</Chip>
            <Chip>query candidates</Chip>
            <Chip>rank & screen</Chip>
            <Chip>caveat & explain</Chip>
          </div>
          <div className="mono mt-2 text-[11px] text-muted">Opus drives the FLOPs — it doesn&rsquo;t do them.</div>
        </div>
        <Down />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Engine
            title="Materials Project"
            tag="LIVE API"
            body="~150K precomputed DFT entries → film candidates (κ, E_g, stability, structure)."
          />
          <Engine
            title="densitygen engine"
            tag="LIVE / CACHED"
            body="ALD precursor screening — 7-axis viability scorecard, MLIP energies when enabled."
            accent
          />
          <Engine
            title="DFT · atomate2"
            tag="VALIDATE"
            body="Confirm only the 2–3 finalists — the expensive step, reserved for the survivors."
          />
        </div>
        <Down />
        <div className="rounded-[2px] border border-hair bg-canvas px-4 py-3">
          <div className="mono text-[11px] tracking-[0.08em] text-faint">RENDERED IN THE APP — THE MODEL OUTPUT</div>
          <div className="mt-1.5 flex flex-wrap gap-2">
            <Chip>ranked shortlist</Chip>
            <Chip>κ × E_g Pareto</Chip>
            <Chip>7-axis precursor scorecard</Chip>
            <Chip>3D surface chemistry</Chip>
            <Chip>provenance &amp; confidence</Chip>
          </div>
        </div>
      </div>

      <p className="mono mt-3 text-[11px] leading-relaxed text-faint">
        Every number carries its source: Materials Project (live), densitygen engine (live or bundled real
        snapshot), and the model backend&rsquo;s own provenance tag. Nothing on screen is invented.
      </p>
    </div>
  );
}

function SectionLabel({ n, title }: { n: string; title: string }) {
  return (
    <div className="mb-2 mt-4 flex items-center gap-2">
      <span className="mono flex h-5 w-5 items-center justify-center rounded-[2px] bg-ink text-[11px] text-white">
        {n}
      </span>
      <span className="mono text-[11px] uppercase tracking-[0.1em] text-muted">{title}</span>
    </div>
  );
}

function Box({
  title,
  sub,
  children,
  dark,
}: {
  title: string;
  sub: string;
  children?: React.ReactNode;
  dark?: boolean;
}) {
  return (
    <div
      className="flex flex-col rounded-[2px] border p-3"
      style={
        dark
          ? { background: "var(--color-strip)", borderColor: "#000", color: "#EDEBE6" }
          : { background: "#fff", borderColor: "var(--color-hair)" }
      }
    >
      <div className="text-[13px] font-semibold" style={{ color: dark ? "#fff" : "var(--color-ink)" }}>
        {title}
      </div>
      <div className="mt-0.5 text-[11.5px]" style={{ color: dark ? "#B9B6AF" : "var(--color-muted)" }}>
        {sub}
      </div>
      {children && <div className="mt-2 flex flex-wrap gap-1.5">{children}</div>}
    </div>
  );
}

function Deploy({ to, url }: { to: string; url: string }) {
  return (
    <div className="mt-1 flex items-center gap-1.5">
      <span className="mono text-[10px] text-faint">deploy →</span>
      <span className="tag tag-amber !py-0.5 !text-[10px]">{to}</span>
      <span className="mono text-[10px] text-muted">{url}</span>
    </div>
  );
}

function Engine({ title, tag, body, accent }: { title: string; tag: string; body: string; accent?: boolean }) {
  return (
    <div
      className="rounded-[2px] border p-3"
      style={{
        background: accent ? "var(--color-amber-tint)" : "#fff",
        borderColor: accent ? "var(--color-amber-border)" : "var(--color-hair)",
      }}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold" style={{ color: accent ? "var(--color-amber-deep)" : "var(--color-ink)" }}>
          {title}
        </span>
        <span className="mono text-[9px] text-faint">{tag}</span>
      </div>
      <div className="mt-1 text-[11.5px] leading-snug text-muted">{body}</div>
    </div>
  );
}

function Lane({ step, title, body, serif }: { step: string; title: string; body: string; serif?: boolean }) {
  return (
    <div className="rounded-[2px] border border-hair bg-canvas px-4 py-3">
      <div className="mono text-[11px] tracking-[0.08em] text-faint">{step}</div>
      <div className="mt-1 text-[14px] font-semibold text-ink">{title}</div>
      <div className={`${serif ? "serif text-[16px]" : "text-[12px]"} mt-1 text-ink2`}>{body}</div>
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return <span className="tag !py-1 !text-[10.5px]">{children}</span>;
}

function Arrow() {
  return <div className="hidden items-center justify-center text-[18px] text-amber md:flex">→</div>;
}

function Down() {
  return <div className="py-1 text-center text-[16px] text-amber">↓</div>;
}

function FlowArrow({ label }: { label: string }) {
  return (
    <div className="my-2 flex items-center gap-3">
      <div className="h-px flex-1 bg-hair" />
      <span className="mono text-[10px] uppercase tracking-[0.08em] text-faint">{label} ↓</span>
      <div className="h-px flex-1 bg-hair" />
    </div>
  );
}
