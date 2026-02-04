export interface ConversationContext {
  recentMessages: { role: string; content: string; topic?: string }[];
  userId: string;
}

export interface Intent {
  intent: DisambiguatedIntent;
  confidence: number;
  plan: ExecutionPlan;
  clarificationQuestions: string[];
}

interface Entity {
  type: string;
  value: string;
  referent?: string; // Resolved reference
}

interface Action {
  verb: string;
  target?: string;
}

interface DisambiguatedIntent {
  type: "INFORMATION_RETRIEVAL" | "TASK_EXECUTION" | "UNKNOWN";
  query?: string;
  action?: string;
  requiredCapability?: string;
  expectedOutcome?: string;
  entities: Entity[];
}

interface ExecutionPlan {
  steps: PlanStep[];
  estimatedDuration: number;
}

interface PlanStep {
  type: "SEARCH" | "SYNTHESIZE" | "PRESENT" | "VALIDATE" | "ACQUIRE_TOKEN" | "EXECUTE" | "VERIFY";
  query?: string;
  sources?: string;
  format?: string;
  params?: any;
  scope?: string;
  action?: string;
  expected?: string;
}

import { TwoTowerEngine } from "./two-tower.js";

export class NaturalIntentParser {
  private readonly twoTower = new TwoTowerEngine();
  private readonly DEFAULT_CONFIDENCE = 0.85;
  private readonly CLARIFICATION_THRESHOLD = 0.7;

  async parseIntent(message: string, context: ConversationContext): Promise<Intent> {
    // Parallel extraction for better performance
    const [entities, actions] = await Promise.all([
      this.extractEntities(message),
      this.extractActions(message),
    ]);

    // Sequential processing with context
    const disambiguated = await this.disambiguate(entities, actions, context);
    const plan = await this.generatePlan(disambiguated);

    return {
      intent: disambiguated,
      confidence: this.DEFAULT_CONFIDENCE,
      plan,
      clarificationQuestions: this.needsClarification()
        ? ["Could you clarify what you mean by 'it'?"]
        : [],
    };
  }

  private needsClarification(): boolean {
    return this.DEFAULT_CONFIDENCE < this.CLARIFICATION_THRESHOLD;
  }

  private async extractEntities(message: string): Promise<Entity[]> {
    const entities: Entity[] = [];

    // Pre-compiled regex for better performance
    const PRONOUN_REGEX = /\b(it|this|that)\b/i;

    if (message.includes("server")) {
      entities.push({ type: "SYSTEM", value: "server" });
    }
    if (PRONOUN_REGEX.test(message)) {
      entities.push({ type: "PRONOUN", value: "it" });
    }

    return entities;
  }

  private async extractActions(message: string): Promise<Action[]> {
    const actions: Action[] = [];

    // Use includes for simple checks
    if (message.includes("fix")) actions.push({ verb: "fix" });
    if (message.includes("check")) actions.push({ verb: "check" });

    return actions;
  }

  private async disambiguate(
    entities: Entity[],
    actions: Action[],
    context: ConversationContext,
  ): Promise<DisambiguatedIntent> {
    try {
      // Attempt TwoTower processing first
      const impulse = await this.twoTower.generateImpulse(
        `Disambiguate Intent for Entities: ${JSON.stringify(entities)} and Actions: ${JSON.stringify(actions)}. ` +
          `Context: ${JSON.stringify(context.recentMessages.slice(-2))}`,
      );

      if (impulse.action !== "error_fallback") {
        return {
          type: impulse.requiresValidation ? "TASK_EXECUTION" : "INFORMATION_RETRIEVAL",
          query: impulse.payload.thought,
          action: impulse.action,
          entities,
        };
      }
    } catch (error) {
      // Log error and fall back to heuristics
      console.debug("TwoTower disambiguation failed, using heuristics:", error);
    }

    // Fallback to optimized heuristic processing
    return this.applyHeuristics(entities, actions, context);
  }

  private applyHeuristics(
    entities: Entity[],
    actions: Action[],
    context: ConversationContext,
  ): DisambiguatedIntent {
    const recentTopics = context.recentMessages
      .map((m) => m.topic)
      .filter(Boolean)
      .slice(-5);

    const resolvedEntities = entities.map((e) =>
      e.type === "PRONOUN" && recentTopics.length > 0
        ? { ...e, referent: recentTopics[recentTopics.length - 1] }
        : e,
    );

    const primaryAction = actions[0];

    switch (primaryAction?.verb) {
      case "check":
        return {
          type: "INFORMATION_RETRIEVAL",
          query: `status of ${resolvedEntities.map((e) => e.referent || e.value).join(" ")}`,
          entities: resolvedEntities,
        };
      case "fix":
        return {
          type: "TASK_EXECUTION",
          action: "REPAIR",
          requiredCapability: "FS_WRITE",
          expectedOutcome: "System operational",
          entities: resolvedEntities,
        };
      default:
        return { type: "UNKNOWN", entities: resolvedEntities };
    }
  }

  private async generatePlan(intent: DisambiguatedIntent): Promise<ExecutionPlan> {
    const planTemplates: Record<string, PlanStep[]> = {
      INFORMATION_RETRIEVAL: [
        { type: "SEARCH", query: intent.query },
        { type: "SYNTHESIZE", sources: "search_results" },
        { type: "PRESENT", format: "summary" },
      ],
      TASK_EXECUTION: [
        { type: "VALIDATE", params: intent.entities },
        { type: "ACQUIRE_TOKEN", scope: intent.requiredCapability },
        { type: "EXECUTE", action: intent.action },
        { type: "VERIFY", expected: intent.expectedOutcome },
      ],
    };

    const steps = planTemplates[intent.type] || [];
    return {
      steps,
      estimatedDuration: steps.length * 1000,
    };
  }
}
