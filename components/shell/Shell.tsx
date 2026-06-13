import { InstrumentStrip } from "./InstrumentStrip";
import { RunContextStrip } from "./RunContextStrip";
import { NavRail } from "./NavRail";
import { AgentTrace } from "./AgentTrace";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full flex-col bg-canvas">
      <InstrumentStrip />
      <RunContextStrip />
      <div className="flex min-h-0 flex-1">
        <NavRail />
        <main className="min-w-0 flex-1 overflow-auto bg-canvas">{children}</main>
        <AgentTrace />
      </div>
    </div>
  );
}
