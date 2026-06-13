import { getCandidateById } from "@/lib/mp/queries";

// GET /api/material/:id → scored candidate + relaxed structure.
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const result = await getCandidateById(id);
  if (!result.candidate) {
    return Response.json({ error: "not found" }, { status: 404 });
  }
  return Response.json(result);
}
