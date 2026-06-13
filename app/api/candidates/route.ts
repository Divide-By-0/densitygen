import { getCandidates } from "@/lib/mp/queries";

// GET /api/candidates → live MP dielectric-oxide candidates (or cached fallback).
export async function GET() {
  const result = await getCandidates();
  return Response.json(result);
}
