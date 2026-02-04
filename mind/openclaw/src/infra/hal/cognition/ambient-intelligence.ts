import { SidecarOrchestrator } from "../physiology/sidecar-orchestrator.js";
import { VisionMemory } from "./vision-memory.js";

interface ContextNode {
  id: string;
  type: string;
  data: any;
  timestamp: number;
}

interface BehaviorPattern {
  userId: string;
  timeOfDay: number; // 0-23
  dayOfWeek: number; // 0-6
  precedingActions: string[];
  likelyNextAction: string;
  occurrences: number;
  frequency: number;
}

interface Prediction {
  action: string;
  confidence: number;
  reasoning: string;
  preparationSteps: PreparationStep[];
}

interface PreparationStep {
  type: "LOAD_MODEL" | "CACHE_DATA" | "OPEN_CHANNEL";
  target: string; // modelName, dataKey, or channelId
}

interface SystemState {
  userId: string;
  activeChannels: string[];
  recentActions: string[];
}

export class AmbientIntelligence {
  private contextGraph: Map<string, ContextNode> = new Map();
  private userPatterns: Map<string, BehaviorPattern[]> = new Map();

  // Dependencies injected or lazily resolved
  constructor(
    private sidecarOrchestrator?: SidecarOrchestrator,
    private memory?: VisionMemory,
  ) {}

  async analyzeContext(currentState: SystemState): Promise<Prediction[]> {
    const timeOfDay = new Date().getHours();
    const dayOfWeek = new Date().getDay();
    const recentActions = currentState.recentActions; // In real impl, fetch from deeper history

    // Pattern matching
    const patterns = this.userPatterns.get(currentState.userId) ?? [];
    const matchingPatterns = patterns.filter(
      (p) =>
        p.timeOfDay === timeOfDay &&
        p.dayOfWeek === dayOfWeek &&
        this.similarActions(p.precedingActions, recentActions),
    );

    // Generate predictions
    const predictions: Prediction[] = [];
    for (const pattern of matchingPatterns) {
      predictions.push({
        action: pattern.likelyNextAction,
        confidence: pattern.frequency / (patterns.length || 1),
        reasoning: `Historical pattern from ${pattern.occurrences} similar contexts`,
        preparationSteps: this.getPreparationSteps(pattern.likelyNextAction),
      });
    }

    return predictions.sort((a, b) => b.confidence - a.confidence);
  }

  async proactivePreparation(predictions: Prediction[]): Promise<void> {
    const topPrediction = predictions[0];
    if (!topPrediction) return;

    if (topPrediction.confidence > 0.7) {
      console.log(`[HAL] 🔮 Proactively preparing for: ${topPrediction.action}`);

      await Promise.all(
        topPrediction.preparationSteps.map(async (step) => {
          switch (step.type) {
            case "LOAD_MODEL":
              // If we have access to the orchestrator, warm up the model
              await this.sidecarOrchestrator?.monitorHealth({ name: step.target } as any); // Placeholder for warmup
              break;
            case "CACHE_DATA":
              // Logic to preload data
              break;
            case "OPEN_CHANNEL":
              // Logic to connect channel
              break;
          }
        }),
      );
    }
  }

  // --- Helper Methods ---

  private similarActions(patternActions: string[], currentActions: string[]): boolean {
    if (patternActions.length === 0) return true;
    const recent = currentActions.slice(-patternActions.length);
    return JSON.stringify(recent) === JSON.stringify(patternActions);
  }

  private getPreparationSteps(action: string): PreparationStep[] {
    // Heuristic map for preparation
    if (action.includes("code")) {
      return [{ type: "LOAD_MODEL", target: "deepseek-coder" }];
    }
    if (action.includes("search")) {
      return [{ type: "CACHE_DATA", target: "search_index" }];
    }
    return [];
  }

  // Public method to record new observations and update patterns
  public observe(userId: string, action: string, context: SystemState) {
    // Update user patterns based on observation
    // This feeds into the predictive model for future context hits
    this.updateUserPatterns(userId, action, context);
  }

  private updateUserPatterns(userId: string, action: string, context: SystemState) {
    const patterns = this.userPatterns.get(userId) ?? [];
    // Simple logic: if a similar pattern exists, increment recurrence
    // Otherwise, start a new pattern
    const existing = patterns.find((p) =>
      this.similarActions(p.precedingActions, context.recentActions),
    );

    if (existing) {
      existing.occurrences++;
      existing.frequency = existing.occurrences / (existing.occurrences + 5); // decay factor
      if (existing.likelyNextAction !== action) {
        // Pattern divergence - maybe spin off new pattern?
      }
    } else {
      patterns.push({
        userId,
        timeOfDay: new Date().getHours(),
        dayOfWeek: new Date().getDay(),
        precedingActions: [...context.recentActions],
        likelyNextAction: action,
        occurrences: 1,
        frequency: 0.1,
      });
    }
    this.userPatterns.set(userId, patterns);
  }
}
