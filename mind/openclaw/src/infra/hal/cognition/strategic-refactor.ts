import { TwoTowerEngine } from "./two-tower.js";

interface PathCost {
  count: number;
  totalDuration: number;
  avgComplexity: number;
}

export interface RefactorProposal {
  path: string;
  reason: string;
  currentCost: number;
  estimatedSavings: number;
  confidence: number;
}

export class StrategicRefactor {
  private costPaths = new Map<string, PathCost>();
  private twoTower = new TwoTowerEngine();

  recordPathCost(path: string, duration: number, complexity: number): void {
    const existing = this.costPaths.get(path) ?? { count: 0, totalDuration: 0, avgComplexity: 0 };

    this.costPaths.set(path, {
      count: existing.count + 1,
      totalDuration: existing.totalDuration + duration,
      avgComplexity: (existing.avgComplexity * existing.count + complexity) / (existing.count + 1),
    });
  }

  async analyzeRefactorOpportunities(): Promise<RefactorProposal[]> {
    const rawProposals: RefactorProposal[] = [];

    for (const [path, cost] of Array.from(this.costPaths.entries())) {
      if (cost.count > 10 && cost.avgComplexity > 50) {
        const roi = this.calculateROI(cost);

        rawProposals.push({
          path,
          reason: "High-frequency, high-complexity path",
          currentCost: cost.totalDuration / cost.count,
          estimatedSavings: roi.savings,
          confidence: roi.confidence,
        });
      }
    }

    // Sort by savings
    const sorted = rawProposals.sort((a, b) => b.estimatedSavings - a.estimatedSavings);

    // Top 3 get "Fast thinking" check or validation
    const verified: RefactorProposal[] = [];
    for (const proposal of sorted.slice(0, 3)) {
      const approved = await this.twoTower.validateAction({
        action: `refactor_path:${proposal.path}`,
        confidence: proposal.confidence,
        risk: "medium",
        payload: { savings: proposal.estimatedSavings, reason: proposal.reason },
        requiresValidation: true,
      });
      if (approved) verified.push(proposal);
    }

    return verified;
  }

  private calculateROI(cost: PathCost): { savings: number; confidence: number } {
    // Simplified model: assume refactoring reduces complexity by 30%
    const savings = (cost.totalDuration / cost.count) * 0.3 * cost.count;
    const confidence = Math.min(cost.count / 100, 1); // More data = higher confidence

    return { savings, confidence };
  }
}
