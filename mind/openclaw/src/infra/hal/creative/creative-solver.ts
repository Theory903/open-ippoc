export interface Problem {
  description: string;
  constraints: string[];
}

export interface Solution {
  concept: string;
  feasibility: number;
  novelty: number;
}

export class CreativeSolver {
  async generateSolutions(problem: Problem): Promise<Solution[]> {
    const solutions: Solution[] = [];

    // 1. Analogical Reasoning (Heuristic)
    const analogies = this.findAnalogies(problem.description);
    for (const analogy of analogies) {
      solutions.push({
        concept: `Apply ${analogy.domain} principle: ${analogy.principle}`,
        feasibility: analogy.relevance * 0.8,
        novelty: 0.9,
      });
    }

    // 2. Inversion (Algorithmic)
    const invertedConstraints = problem.constraints.map((c) => `NOT(${c})`);
    solutions.push({
      concept: `Invert constraints: ${invertedConstraints.join(", ")}`,
      feasibility: 0.5,
      novelty: 0.8,
    });

    return solutions.sort((a, b) => b.novelty + b.feasibility - (a.novelty + a.feasibility));
  }

  private findAnalogies(
    description: string,
  ): { domain: string; principle: string; relevance: number }[] {
    const keywords = description.toLowerCase().split(" ");
    const knowledgeBase = [
      {
        domain: "Biology",
        principle: "Evolution/Selection",
        triggers: ["optimize", "select", "grow"],
      },
      { domain: "Physics", principle: "Entropy/Chaos", triggers: ["random", "disorder", "mess"] },
      { domain: "Economics", principle: "Market/Trade", triggers: ["value", "exchange", "cost"] },
      { domain: "Computing", principle: "Cache/Index", triggers: ["fast", "search", "find"] },
    ];

    return knowledgeBase
      .map((kb) => ({
        ...kb,
        relevance:
          kb.triggers.filter((t) => keywords.some((k) => k.includes(t))).length /
          kb.triggers.length,
      }))
      .filter((match) => match.relevance > 0);
  }
}
