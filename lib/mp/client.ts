// Server-only Materials Project REST client.
// The API key is read from MP_API_KEY and never reaches the browser.

const BASE = "https://api.materialsproject.org";

export class MPError extends Error {}

type Params = Record<string, string | number | undefined>;

export async function mpFetch(path: string, params: Params): Promise<{
  data: Record<string, unknown>[];
  meta: { total_doc: number };
}> {
  const key = process.env.MP_API_KEY;
  if (!key) throw new MPError("MP_API_KEY is not set");

  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) url.searchParams.set(k, String(v));
  }

  let res: Response;
  try {
    res = await fetch(url, {
      headers: { "X-API-KEY": key, Accept: "application/json" },
      signal: AbortSignal.timeout(9000),
      next: { revalidate: 3600 },
    });
  } catch (e) {
    throw new MPError(`MP request failed: ${(e as Error).message}`);
  }
  if (!res.ok) throw new MPError(`MP responded ${res.status}`);
  return res.json();
}

export const hasMPKey = () => Boolean(process.env.MP_API_KEY);
