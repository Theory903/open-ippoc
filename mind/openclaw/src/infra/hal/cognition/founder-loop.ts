import { SelfHiring } from "../evolution/self-hiring.js";
import { MarketSensing } from "./market-sensing.js";
import { OpportunityDetector } from "./opportunity-detector.js";
import { StrategicRefactor } from "./strategic-refactor.js";
import { VisionMemory } from "./vision-memory.js";

export class FounderLoop {
  private opportunityDetector: OpportunityDetector;
  private strategicRefactor: StrategicRefactor;
  private visionMemory: VisionMemory;
  private marketSensing: MarketSensing;
  private selfHiring: SelfHiring;

  constructor(
    opportunityDetector: OpportunityDetector,
    strategicRefactor: StrategicRefactor,
    visionMemory: VisionMemory,
  ) {
    this.opportunityDetector = opportunityDetector;
    this.strategicRefactor = strategicRefactor;
    this.visionMemory = visionMemory;
    this.marketSensing = new MarketSensing();
    this.selfHiring = new SelfHiring();
  }

  // Daily cognition loop (runs autonomously)
  async founderModeCycle() {
    console.log("[HAL] 🧠 Starting Founder Mode Cycle...");

    // 1. Opportunity Detection & Market Sensing
    const opportunities = await this.opportunityDetector.getAllOpportunities(); // Assuming method exists or we add it
    const marketGaps = await this.marketSensing.analyzeTrends();

    // 2. Strategic Refactoring
    const refactors = await this.strategicRefactor.analyzeRefactorOpportunities();

    // 3. Vision Alignment
    const progress = await this.visionMemory.evaluateProgress();

    // 4. Decision Making (Prioritize)
    const combinedActions = [
      ...opportunities.map((o) => ({ category: "OPPORTUNITY", ...o, value: o.estimatedValue })),
      ...marketGaps.map((g) => ({
        category: "MARKET",
        description: g.description,
        value: g.monetizationPotential * 100,
      })),
      ...refactors.map((r) => ({
        category: "REFACTOR",
        description: `Refactor ${r.path}`,
        value: r.estimatedSavings,
      })),
    ];

    const actions = this.prioritizeActions(combinedActions, progress);

    // 5. Execute Top Action (with Brain approval)
    if (actions.length > 0) {
      const topAction = actions[0];
      console.log(
        `[HAL] 🚀 Proposing Top Strategic Action: ${topAction.description} (Value: ${topAction.value})`,
      );

      await this.submitToBrain({
        type: "STRATEGIC_PROPOSAL",
        action: topAction,
        reasoning: `Selected based on value ${topAction.value} and vision alignment.`,
      });

      // Self-Hiring check: If action is complex, spawn a cell
      if (topAction.value > 80) {
        await this.selfHiring.spawnCell({
          role: "SPECIALIST",
          description: `Execute ${topAction.description}`,
          budgetCap: 100,
        });
      }
    }

    // Maintenance
    await this.selfHiring.evaluateCells();
  }

  private prioritizeActions(actions: any[], progress: any): any[] {
    // Sort by value desc
    return actions.sort((a, b) => b.value - a.value);
  }

  private async submitToBrain(proposal: any) {
    // Brain Uplink
    // In a distributed system, this sends to the Cortex service.
    // Here, we log to the structured Uplink stream.
    console.log(
      "[BRAIN_UPLINK] 📤 Proposal Submitted:",
      JSON.stringify({
        timestamp: Date.now(),
        ...proposal,
      }),
    );
  }
}
