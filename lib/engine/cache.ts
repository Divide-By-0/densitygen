import cacheRaw from "../data/screen-cache.json";
import type { ScreenResponse } from "./types";

// Real engine output captured from the live backend, bundled so the Vercel app
// can demo on its own (single surface) when the screening backend is slow/down.
// These are genuine model results — not invented — just snapshotted.
const CACHE = cacheRaw as unknown as Record<string, ScreenResponse>;

export function cachedScreen(film: string): ScreenResponse | null {
  return CACHE[film] ?? null;
}
