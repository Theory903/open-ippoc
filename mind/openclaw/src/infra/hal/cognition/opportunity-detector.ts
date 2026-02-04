import { TwoTowerEngine } from "./two-tower.js";

export interface Opportunity {
  type: "MISSING_CAPABILITY" | "OPTIMIZATION" | "NEW_PRODUCT";
  description: string;
  frequency: number;
  suggestedAction: string;
  estimatedValue: number;
}

export class OpportunityDetector {
  private failurePatterns = new Map<string, number>();
  private missingTools = new Set<string>();
  private twoTower = new TwoTowerEngine();

  async recordFailure(task: string, reason: string): Promise<void> {
    const pattern = await this.extractPattern(task, reason);
    const count = (this.failurePatterns.get(pattern) ?? 0) + 1;
    this.failurePatterns.set(pattern, count);

    if (count >= 3) {
      this.proposeOpportunity(pattern, count);
    }
  }

  recordMissingTool(toolName: string): void {
    this.missingTools.add(toolName);
  }

  async getAllOpportunities(): Promise<Opportunity[]> {
    const opportunities: Opportunity[] = [];

    // Convert failures to opportunities
    for (const [pattern, count] of Array.from(this.failurePatterns.entries())) {
      if (count >= 3) {
        opportunities.push({
          type: "MISSING_CAPABILITY",
          description: `Repeated failure pattern: ${pattern}`,
          frequency: count,
          suggestedAction: `Create new tool or plugin to handle: ${pattern}`,
          estimatedValue: this.estimateValue(count),
        });
      }
    }

    return opportunities;
  }

  async proposeOpportunity(pattern: string, frequency: number): Promise<void> {
    const opportunity: Opportunity = {
      type: "MISSING_CAPABILITY",
      description: `Repeated failure pattern: ${pattern}`,
      frequency,
      suggestedAction: `Create new tool or plugin to handle: ${pattern}`,
      estimatedValue: this.estimateValue(frequency),
    };

    // Use Tower B to validate if this is a real opportunity vs noise
    const approved = await this.twoTower.validateAction({
      action: "recognize_opportunity",
      confidence: 0.7,
      risk: "low",
      payload: opportunity,
      requiresValidation: true,
    });

    if (approved) {
      await this.notifyBrain(opportunity);
    }
  }

  private async extractPattern(task: string, reason: string): Promise<string> {
    // Ported from Heuristic to impulse-based logic
    const impulse = await this.twoTower.generateImpulse(
      `Identify failure pattern for Task: "${task}" with Reason: "${reason}"`,
    );

    if (impulse.action === "unknown") {
      // Fallback to heuristics
      if (reason.includes("timeout")) return "timeout-prone-tasks";
      if (reason.includes("rate limit")) return "rate-limited-operations";
      return "general-failure";
    }

    return impulse.action;
  }

  private estimateValue(frequency: number): number {
    // Ported from simple model to weighted frequency
    return frequency * 5 * (1 + frequency / 10);
  }

  private async notifyBrain(opportunity: Opportunity): Promise<void> {
    console.log("💡 OPPORTUNITY DETECTED:", opportunity);
    // Send to Brain for evaluation
  }
}
