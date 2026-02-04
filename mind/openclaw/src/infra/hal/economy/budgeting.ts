import { getIPPOCAdapter } from "../../../../../../brain/cortex/openclaw-cortex/src/ippoc-adapter.js";

type BudgetBucket = "survival" | "earning" | "learning" | "reserve" | "growth";

interface EconomicDecision {
  decision: "approve" | "reject";
  approvedBudget: number;
  reason: string;
  bucket: BudgetBucket;
}

export class EconomicBrain {
  private adapter = getIPPOCAdapter();

  // Budget allocation weights (Could be dynamic later)
  private buckets: Record<BudgetBucket, number> = {
    survival: 0.5,
    earning: 0.25,
    learning: 0.1,
    reserve: 0.1,
    growth: 0.05,
  };

  async getWalletBalance(): Promise<number> {
    return this.adapter.getBalance();
  }

  async evaluateInvestment(
    requiredBudget: number,
    confidence: number,
    risk: "low" | "medium" | "high",
  ): Promise<EconomicDecision> {
    const balance = await this.getWalletBalance();

    // Rule 1: Safety Envelope (Never bet >10% of liquid cash on one idea unless survival)
    const maxBet = balance * 0.1;

    if (requiredBudget > maxBet) {
      return {
        decision: "reject",
        approvedBudget: 0,
        reason: `Request (${requiredBudget}) exceeds 10% safety cap (${maxBet})`,
        bucket: "reserve",
      };
    }

    // Rule 2: Confidence Threshold
    if (confidence < 0.6) {
      return {
        decision: "reject",
        approvedBudget: 0,
        reason: "Confidence below 0.6 threshold",
        bucket: "learning",
      };
    }

    // Rule 3: Bucket Allocation
    // Simple heuristic: If risk is low/med, use 'earning'. If high, use 'growth'.
    const bucket: BudgetBucket = risk === "high" ? "growth" : "earning";

    return {
      decision: "approve",
      approvedBudget: requiredBudget,
      reason: "Within safety envelope and confidence threshold",
      bucket,
    };
  }
}
