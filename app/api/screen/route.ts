import { getScorecard } from "@/lib/engine/queries";
import { screenPrecursors } from "@/lib/engine/client";
import { cachedScreen } from "@/lib/engine/cache";
import type { CandidateInput } from "@/lib/engine/types";

// POST /api/screen
//  - { formula, useMl? }                      → screen the film matching a material
//  - { film, coReactant?, candidates, useMl? } → screen an explicit candidate set
// Proxied to the screening backend; used by the client screening console + viewer.
export async function POST(req: Request) {
  let body: {
    formula?: string;
    film?: string;
    coReactant?: string;
    candidates?: CandidateInput[];
    useMl?: boolean;
  };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "bad request" }, { status: 400 });
  }

  // explicit candidate set
  if (body.film && body.candidates?.length) {
    try {
      const response = await screenPrecursors({
        film: body.film,
        co_reactant: body.coReactant,
        temperature_max_c: 350,
        candidates: body.candidates,
        use_ml_potential: body.useMl ?? false,
      });
      return Response.json({ supported: true, film: body.film, response, source: "live" });
    } catch {
      const snap = cachedScreen(body.film);
      if (snap) return Response.json({ supported: true, film: body.film, response: snap, source: "cached" });
      return Response.json({ supported: false, error: "engine unavailable" }, { status: 200 });
    }
  }

  // resolve from a material formula
  if (!body.formula) return Response.json({ error: "formula or film+candidates required" }, { status: 400 });
  const result = await getScorecard(body.formula, body.useMl ?? false);
  if (!result) return Response.json({ supported: false }, { status: 200 });
  return Response.json({ supported: true, ...result });
}
