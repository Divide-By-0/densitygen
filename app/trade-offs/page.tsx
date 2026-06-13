import { getCandidates } from "@/lib/mp/queries";
import { ParetoExplorer } from "@/components/screens/ParetoExplorer";

export const dynamic = "force-dynamic";

export default async function TradeOffsPage() {
  const { candidates } = await getCandidates();
  return <ParetoExplorer candidates={candidates} />;
}
