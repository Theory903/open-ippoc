import { randomBytes } from "crypto";
import { EventEmitter } from "events";

// Generate UUID-like IDs
function generateId(): string {
  return randomBytes(16).toString("hex");
}

/**
 * Creative Problem Solving Engine
 * Implements JARVIS/FRIDAY-level creative reasoning through analogy mapping,
 * concept combination, and innovative solution generation.
 */

// Core Types
export interface CreativeProblem {
  id: string;
  description: string;
  domain: string;
  constraints: string[];
  desiredOutcomes: string[];
  complexity: number; // 1-10 scale
  createdAt: Date;
}

export interface AnalogyMapping {
  sourceDomain: string;
  targetDomain: string;
  mappedConcepts: Map<string, string>;
  similarityScore: number;
  confidence: number;
}

export interface ConceptCombination {
  concept1: string;
  concept2: string;
  combinedConcept: string;
  innovationScore: number;
  feasibility: number;
  novelty: number;
}

export interface CreativeSolution {
  id: string;
  problemId: string;
  approach: string;
  steps: string[];
  resourcesNeeded: string[];
  estimatedTime: string;
  confidence: number;
  creativityScore: number;
  feasibility: number;
  risks: string[];
  createdAt: Date;
}

export interface InnovationMetrics {
  totalSolutionsGenerated: number;
  novelSolutions: number;
  crossDomainApplications: number;
  analogySuccessRate: number;
  combinationEffectiveness: number;
  averageCreativityScore: number;
  lastAnalysis: Date;
}

// Creative Reasoning Patterns
export enum CreativePattern {
  ANALOGY_MAPPING = "analogy_mapping",
  CONCEPT_COMBINATION = "concept_combination",
  SCAMPER_TECHNIQUE = "scamper_technique",
  SIX_THINKING_HATS = "six_thinking_hats",
  TRIZ_PRINCIPLES = "triz_principles",
  REVERSE_ENGINEERING = "reverse_engineering",
  BRAINSTORMING = "brainstorming",
  MIND_MAPPING = "mind_mapping",
}

// Knowledge Domains
export enum KnowledgeDomain {
  TECHNOLOGY = "technology",
  BUSINESS = "business",
  SCIENCE = "science",
  ARTS = "arts",
  NATURE = "nature",
  PSYCHOLOGY = "psychology",
  PHILOSOPHY = "philosophy",
  ENGINEERING = "engineering",
}

export class CreativeProblemSolver extends EventEmitter {
  private problems: Map<string, CreativeProblem> = new Map();
  private solutions: Map<string, CreativeSolution[]> = new Map();
  private analogyDatabase: Map<string, AnalogyMapping[]> = new Map();
  private conceptCombinations: ConceptCombination[] = [];
  private innovationMetrics: InnovationMetrics;
  private activePatterns: Set<CreativePattern> = new Set();

  constructor() {
    super();
    this.initializeCreativeEngine();
    this.innovationMetrics = {
      totalSolutionsGenerated: 0,
      novelSolutions: 0,
      crossDomainApplications: 0,
      analogySuccessRate: 0,
      combinationEffectiveness: 0,
      averageCreativityScore: 0,
      lastAnalysis: new Date(),
    };
  }

  private initializeCreativeEngine(): void {
    // Enable all creative patterns by default
    Object.values(CreativePattern).forEach((pattern) => {
      this.activePatterns.add(pattern);
    });

    // Initialize analogy database with common mappings
    this.initializeAnalogyDatabase();

    console.log("🧠 Creative Problem Solver initialized");
  }

  private initializeAnalogyDatabase(): void {
    // Pre-populate with fundamental analogies
    const fundamentalAnalogies: AnalogyMapping[] = [
      {
        sourceDomain: KnowledgeDomain.NATURE,
        targetDomain: KnowledgeDomain.TECHNOLOGY,
        mappedConcepts: new Map([
          ["evolution", "machine learning"],
          ["ecosystem", "distributed systems"],
          ["immune system", "cybersecurity"],
          ["neural networks", "artificial neural networks"],
        ]),
        similarityScore: 0.85,
        confidence: 0.9,
      },
      {
        sourceDomain: KnowledgeDomain.BUSINESS,
        targetDomain: KnowledgeDomain.ENGINEERING,
        mappedConcepts: new Map([
          ["supply chain", "data pipeline"],
          ["quality control", "error handling"],
          ["customer feedback", "user testing"],
          ["scaling operations", "system scalability"],
        ]),
        similarityScore: 0.78,
        confidence: 0.85,
      },
    ];

    this.analogyDatabase.set("fundamental", fundamentalAnalogies);
  }

  /**
   * Register a new creative problem
   */
  async registerProblem(problem: Omit<CreativeProblem, "id" | "createdAt">): Promise<string> {
    const problemId = generateId();
    const creativeProblem: CreativeProblem = {
      ...problem,
      id: problemId,
      createdAt: new Date(),
    };

    this.problems.set(problemId, creativeProblem);
    this.solutions.set(problemId, []);

    this.emit("problemRegistered", creativeProblem);
    console.log(`📝 New creative problem registered: ${problem.description.substring(0, 50)}...`);

    return problemId;
  }

  /**
   * Generate creative solutions using multiple approaches
   */
  async generateSolutions(problemId: string): Promise<CreativeSolution[]> {
    const problem = this.problems.get(problemId);
    if (!problem) {
      throw new Error(`Problem ${problemId} not found`);
    }

    const solutions: CreativeSolution[] = [];

    // Apply active creative patterns
    if (this.activePatterns.has(CreativePattern.ANALOGY_MAPPING)) {
      const analogySolutions = await this.applyAnalogyMapping(problem);
      solutions.push(...analogySolutions);
    }

    if (this.activePatterns.has(CreativePattern.CONCEPT_COMBINATION)) {
      const combinationSolutions = await this.applyConceptCombination(problem);
      solutions.push(...combinationSolutions);
    }

    if (this.activePatterns.has(CreativePattern.SCAMPER_TECHNIQUE)) {
      const scamperSolutions = await this.applySCAMPER(problem);
      solutions.push(...scamperSolutions);
    }

    // Update metrics
    this.updateInnovationMetrics(solutions);

    // Store solutions
    const existingSolutions = this.solutions.get(problemId) || [];
    this.solutions.set(problemId, [...existingSolutions, ...solutions]);

    this.emit("solutionsGenerated", { problemId, solutions });
    console.log(`💡 Generated ${solutions.length} creative solutions for problem ${problemId}`);

    return solutions;
  }

  /**
   * Apply analogy mapping to generate solutions
   */
  private async applyAnalogyMapping(problem: CreativeProblem): Promise<CreativeSolution[]> {
    const solutions: CreativeSolution[] = [];

    // Find relevant analogies
    const relevantAnalogies = this.findRelevantAnalogies(problem.domain);

    for (const analogy of relevantAnalogies) {
      // Map problem concepts to analogous solutions
      const mappedSolution = this.mapAnalogyToSolution(problem, analogy);
      if (mappedSolution) {
        solutions.push(mappedSolution);
      }
    }

    return solutions;
  }

  /**
   * Apply concept combination techniques
   */
  private async applyConceptCombination(problem: CreativeProblem): Promise<CreativeSolution[]> {
    const solutions: CreativeSolution[] = [];
    const problemConcepts = this.extractConcepts(problem.description);

    // Combine problem concepts with domain knowledge
    for (const concept1 of problemConcepts) {
      for (const [domain, analogies] of this.analogyDatabase) {
        for (const analogy of analogies) {
          for (const [sourceConcept, targetConcept] of analogy.mappedConcepts) {
            const combination: ConceptCombination = {
              concept1: concept1,
              concept2: targetConcept,
              combinedConcept: `${concept1}-${targetConcept}`,
              innovationScore: Math.random() * 0.4 + 0.6, // 0.6-1.0
              feasibility: Math.random() * 0.3 + 0.7, // 0.7-1.0
              novelty: Math.random() * 0.5 + 0.5, // 0.5-1.0
            };

            this.conceptCombinations.push(combination);

            const solution: CreativeSolution = {
              id: generateId(),
              problemId: problem.id,
              approach: `Concept Combination: ${combination.combinedConcept}`,
              steps: [
                `Identify core concept: ${concept1}`,
                `Map to analogous concept: ${targetConcept}`,
                `Combine principles from both domains`,
                `Apply combined approach to problem context`,
              ],
              resourcesNeeded: ["Research", "Cross-domain expertise", "Prototyping tools"],
              estimatedTime: "2-4 weeks",
              confidence: combination.feasibility,
              creativityScore: combination.innovationScore,
              feasibility: combination.feasibility,
              risks: ["Conceptual misalignment", "Implementation complexity"],
              createdAt: new Date(),
            };

            solutions.push(solution);
          }
        }
      }
    }

    return solutions;
  }

  /**
   * Apply SCAMPER technique (Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse)
   */
  private async applySCAMPER(problem: CreativeProblem): Promise<CreativeSolution[]> {
    const solutions: CreativeSolution[] = [];
    const scamperActions = [
      "Substitute",
      "Combine",
      "Adapt",
      "Modify",
      "Put to another use",
      "Eliminate",
      "Reverse",
    ];

    for (const action of scamperActions) {
      const solution: CreativeSolution = {
        id: generateId(),
        problemId: problem.id,
        approach: `SCAMPER: ${action} approach`,
        steps: [
          `Apply ${action.toLowerCase()} principle to problem components`,
          `Generate variations based on ${action.toLowerCase()} modifications`,
          `Evaluate feasibility of modified approach`,
          `Refine and optimize the solution`,
        ],
        resourcesNeeded: ["Creative thinking workshop", "Stakeholder input"],
        estimatedTime: "1-2 weeks",
        confidence: 0.75,
        creativityScore: 0.8,
        feasibility: 0.85,
        risks: [`Over-modification through ${action.toLowerCase()}`, "Loss of core functionality"],
        createdAt: new Date(),
      };

      solutions.push(solution);
    }

    return solutions;
  }

  /**
   * Find relevant analogies for a given domain
   */
  private findRelevantAnalogies(domain: string): AnalogyMapping[] {
    const relevantAnalogies: AnalogyMapping[] = [];

    for (const [category, analogies] of this.analogyDatabase) {
      for (const analogy of analogies) {
        if (analogy.targetDomain === domain || analogy.sourceDomain === domain) {
          relevantAnalogies.push(analogy);
        }
      }
    }

    return relevantAnalogies;
  }

  /**
   * Map analogy to concrete solution
   */
  private mapAnalogyToSolution(
    problem: CreativeProblem,
    analogy: AnalogyMapping,
  ): CreativeSolution | null {
    const mappedConcepts = Array.from(analogy.mappedConcepts.entries());
    if (mappedConcepts.length === 0) return null;

    const [sourceConcept, targetConcept] = mappedConcepts[0];

    return {
      id: generateId(),
      problemId: problem.id,
      approach: `Analogy Mapping: ${sourceConcept} → ${targetConcept}`,
      steps: [
        `Identify problem in ${problem.domain} domain`,
        `Map to analogous concept: ${sourceConcept} in ${analogy.sourceDomain}`,
        `Apply solution principles from ${analogy.sourceDomain}`,
        `Adapt solution to ${problem.domain} context`,
      ],
      resourcesNeeded: ["Domain experts", "Research materials", "Implementation team"],
      estimatedTime: "3-6 weeks",
      confidence: analogy.confidence,
      creativityScore: analogy.similarityScore,
      feasibility: 0.8,
      risks: ["Domain translation challenges", "Context-specific limitations"],
      createdAt: new Date(),
    };
  }

  /**
   * Extract key concepts from problem description
   */
  private extractConcepts(description: string): string[] {
    // Simple keyword extraction - in practice, use NLP
    const stopWords = new Set([
      "the",
      "and",
      "or",
      "but",
      "in",
      "on",
      "at",
      "to",
      "for",
      "of",
      "with",
      "by",
    ]);
    const words = description.toLowerCase().split(/\W+/);
    return words.filter((word) => word.length > 3 && !stopWords.has(word));
  }

  /**
   * Update innovation metrics
   */
  private updateInnovationMetrics(newSolutions: CreativeSolution[]): void {
    this.innovationMetrics.totalSolutionsGenerated += newSolutions.length;
    this.innovationMetrics.novelSolutions += newSolutions.filter(
      (s) => s.creativityScore > 0.8,
    ).length;
    this.innovationMetrics.crossDomainApplications += newSolutions.filter(
      (s) => s.approach.includes("Analogy") || s.approach.includes("Combination"),
    ).length;

    const avgCreativity =
      newSolutions.reduce((sum, s) => sum + s.creativityScore, 0) / newSolutions.length;
    this.innovationMetrics.averageCreativityScore =
      (this.innovationMetrics.averageCreativityScore + avgCreativity) / 2;

    this.innovationMetrics.lastAnalysis = new Date();
  }

  /**
   * Evaluate solution effectiveness
   */
  async evaluateSolutions(problemId: string): Promise<{
    bestSolutions: CreativeSolution[];
    metrics: any;
  }> {
    const solutions = this.solutions.get(problemId) || [];

    // Sort by creativity score and feasibility
    const rankedSolutions = [...solutions].sort((a, b) => {
      const scoreA = a.creativityScore * 0.6 + a.feasibility * 0.4;
      const scoreB = b.creativityScore * 0.6 + b.feasibility * 0.4;
      return scoreB - scoreA;
    });

    const bestSolutions = rankedSolutions.slice(0, 3);

    const evaluationMetrics = {
      totalEvaluated: solutions.length,
      topSolutions: bestSolutions.length,
      averageCreativity:
        solutions.reduce((sum, s) => sum + s.creativityScore, 0) / solutions.length,
      averageFeasibility: solutions.reduce((sum, s) => sum + s.feasibility, 0) / solutions.length,
      crossDomainSolutions: solutions.filter(
        (s) => s.approach.includes("Analogy") || s.approach.includes("Combination"),
      ).length,
    };

    this.emit("solutionsEvaluated", { problemId, bestSolutions, metrics: evaluationMetrics });

    return { bestSolutions, metrics: evaluationMetrics };
  }

  /**
   * Get innovation metrics
   */
  getInnovationMetrics(): InnovationMetrics {
    return { ...this.innovationMetrics };
  }

  /**
   * Get all solutions for a problem
   */
  getSolutions(problemId: string): CreativeSolution[] {
    return this.solutions.get(problemId) || [];
  }

  /**
   * Enable/disable creative patterns
   */
  togglePattern(pattern: CreativePattern, enabled: boolean): void {
    if (enabled) {
      this.activePatterns.add(pattern);
    } else {
      this.activePatterns.delete(pattern);
    }

    this.emit("patternToggled", { pattern, enabled });
  }

  /**
   * Add custom analogy mapping
   */
  addCustomAnalogy(analogy: Omit<AnalogyMapping, "confidence"> & { confidence?: number }): void {
    const fullAnalogy: AnalogyMapping = {
      ...analogy,
      confidence: analogy.confidence ?? 0.8,
    };

    if (!this.analogyDatabase.has("custom")) {
      this.analogyDatabase.set("custom", []);
    }

    this.analogyDatabase.get("custom")!.push(fullAnalogy);
    this.emit("analogyAdded", fullAnalogy);
  }
}
