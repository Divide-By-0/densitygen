import { redirect } from "next/navigation";
import { getCandidates } from "@/lib/mp/queries";

export const dynamic = "force-dynamic";

// /material with no id → open the top-ranked candidate.
export default async function MaterialIndex() {
  const { candidates } = await getCandidates();
  redirect(`/material/${candidates[0].id}`);
}
