export interface Observation {
  variable: string;
  value: any;
  timestamp: number;
}

export interface DataPoint {
  [key: string]: any;
  timestamp: number;
}

export interface CausalExplanation {
  mostLikelyCause: CausalEffect;
  alternativeCauses: CausalEffect[];
  confidence: number;
  interventionRecommendations: Intervention[];
}

export interface CausalEffect {
  cause: string;
  effect: string;
  strength: number; // 0-1
  confidence: number; // 0-1
}

export interface Intervention {
  action: "AMPLIFY" | "MITIGATE";
  target: string;
  expectedOutcome: string;
  confidence: number;
}

import { TwoTowerEngine } from "./two-tower.js";

export interface CausalNode {
  id: string;
  parents: string[];
  children: string[];
}

export class CausalInferenceEngine {
  private causalGraph: Map<string, CausalNode> = new Map();
  private twoTower = new TwoTowerEngine();

  async inferCausality(
    observation: Observation,
    historicalData: DataPoint[],
  ): Promise<CausalExplanation> {
    // 1. Build causal graph from data (Heuristic structure discovery)
    await this.buildCausalGraph(historicalData);

    // 2. Identify potential causes for observation
    const candidates = this.findCandidateCauses(observation.variable);

    // 3. Use counterfactual reasoning to estimate effects
    const causalEffects = await Promise.all(
      candidates.map((causeVariable) =>
        this.estimateCausalEffect(causeVariable, observation, historicalData),
      ),
    );

    // 4. Rank by strength
    const ranked = causalEffects.sort((a, b) => b.strength - a.strength);

    // 5. Generate recommendations
    const topCause = ranked[0];
    const interventions = topCause ? await this.suggestInterventions(topCause) : [];

    return {
      mostLikelyCause: topCause,
      alternativeCauses: ranked.slice(1, 4),
      confidence: topCause?.strength ?? 0,
      interventionRecommendations: interventions,
    };
  }

  // --- Causal Analysis Engine ---

  private async buildCausalGraph(data: DataPoint[]) {
    this.causalGraph.clear();

    if (data.length < 2) return;

    const keys = Object.keys(data[0]).filter((k) => k !== "timestamp");

    // Calculate correlation matrix
    for (const cause of keys) {
      for (const effect of keys) {
        if (cause === effect) continue;

        const correlation = this.pearsonCorrelation(data, cause, effect);

        // If highly correlated and cause happens *before* effect (Granger-ish heuristic)
        // For this simple batch check, we just use absolute correlation
        if (Math.abs(correlation) > 0.7) {
          this.addEdge(cause, effect);
        }
      }
    }
  }

  private addEdge(parent: string, child: string) {
    if (!this.causalGraph.has(parent)) {
      this.causalGraph.set(parent, { id: parent, parents: [], children: [] });
    }
    if (!this.causalGraph.has(child)) {
      this.causalGraph.set(child, { id: child, parents: [], children: [] });
    }

    this.causalGraph.get(parent)!.children.push(child);
    this.causalGraph.get(child)!.parents.push(parent);
  }

  private pearsonCorrelation(data: DataPoint[], keyX: string, keyY: string): number {
    const n = data.length;
    let sumX = 0,
      sumY = 0,
      sumXY = 0,
      sumX2 = 0,
      sumY2 = 0;

    for (const point of data) {
      const x = Number(point[keyX]) || 0;
      const y = Number(point[keyY]) || 0;
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
      sumY2 += y * y;
    }

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

    if (denominator === 0) return 0;
    return numerator / denominator;
  }

  private findCandidateCauses(effectVariable: string): string[] {
    // Traverse graph backwards
    const node = this.causalGraph.get(effectVariable);
    return node ? node.parents : [];
  }

  private async estimateCausalEffect(
    cause: string,
    effect: Observation,
    data: DataPoint[],
  ): Promise<CausalEffect> {
    // Counterfactual: What if cause didn't happen?
    const causeHappened = data.filter((d) => Boolean(d[cause]));
    const causeDidNotHappen = data.filter((d) => !d[cause]);

    if (causeHappened.length === 0 || causeDidNotHappen.length === 0) {
      return { cause, effect: effect.variable, strength: 0, confidence: 0 };
    }

    // Simple average treatment effect (ATE)
    const avgOutcomeWithCause = this.avgOutcome(causeHappened, effect.variable);
    const avgOutcomeWithoutCause = this.avgOutcome(causeDidNotHappen, effect.variable);

    const strength = Math.abs(avgOutcomeWithCause - avgOutcomeWithoutCause); // Simplified

    return {
      cause,
      effect: effect.variable,
      strength: strength, // Normalize 0-1
      confidence: Math.min(causeHappened.length, causeDidNotHappen.length) / 100, // Confidence based on sample size
    };
  }

  private async suggestInterventions(cause: CausalEffect): Promise<Intervention[]> {
    const rawInterventions: Intervention[] = [
      {
        action: "MITIGATE",
        target: cause.cause,
        expectedOutcome: `Reduce probability of ${cause.effect}`,
        confidence: cause.confidence,
      },
    ];

    // Use Tower B to validate intervention risk
    const verified: Intervention[] = [];
    for (const intervention of rawInterventions) {
      const approved = await this.twoTower.validateAction({
        action: `intervention:${intervention.action}:${intervention.target}`,
        confidence: intervention.confidence,
        risk: "medium",
        payload: intervention,
        requiresValidation: true,
      });
      if (approved) verified.push(intervention);
    }

    return verified;
  }

  private avgOutcome(data: DataPoint[], variable: string): number {
    const sum = data.reduce((acc, d) => acc + (Number(d[variable]) || 0), 0);
    return sum / (data.length || 1);
  }
}
