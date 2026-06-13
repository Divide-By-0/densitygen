import { screenPrecursors } from "@/lib/engine/client";
import { cachedScreen } from "@/lib/engine/cache";
import { SCENARIOS } from "@/lib/data/scenarios";
import { ScreeningConsole } from "@/components/screens/ScreeningConsole";
import type { ScreenResponse } from "@/lib/engine/types";

export const dynamic = "force-dynamic";

export default async function IntakePage() {
  const s = SCENARIOS[0]; // Mo interconnect — the pitch hero
  let initial: ScreenResponse | null = null;
  let source: "live" | "cached" = "live";
  try {
    initial = await screenPrecursors({
      film: s.film,
      co_reactant: s.coReactant,
      temperature_max_c: 350,
      candidates: s.candidates,
      use_ml_potential: false,
    });
  } catch {
    initial = cachedScreen(s.film);
    source = "cached";
  }
  return (
    <ScreeningConsole
      initialKey={s.key}
      initialFilm={s.film}
      initialResponse={initial}
      initialSource={source}
    />
  );
}
