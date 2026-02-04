export interface SystemSpec {
  inputs: InputSpec[];
  statefulOps: OperationSpec[];
  resources: ResourceSpec[];
}

interface InputSpec {
  name: string;
  type: "string" | "number" | "json";
  validation?: string;
}

interface OperationSpec {
  name: string;
  reads: string[];
  writes: string[];
}

interface ResourceSpec {
  type: "cpu" | "memory" | "disk" | "net";
  quota: number;
}

export interface Vulnerability {
  type: "INPUT_VALIDATION" | "RACE_CONDITION" | "RESOURCE_EXHAUSTION";
  severity: "HIGH" | "MEDIUM" | "LOW";
  description: string;
  mitigation: string;
}

export interface AttackScenario {
  name: string;
  vector: string;
  likelihood: number;
  impact: string;
}

import { TwoTowerEngine } from "./two-tower.js";

export class AdversarialAnalyzer {
  private twoTower = new TwoTowerEngine();

  async findVulnerabilities(system: SystemSpec): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];

    // 1. Input fuzzing - what if user sends malformed data?
    const fuzzTests = this.generateFuzzTests(system.inputs);
    for (const test of fuzzTests) {
      const result = this.simulateInput(test);
      if (result.crashed) {
        vulnerabilities.push({
          type: "INPUT_VALIDATION",
          severity: "HIGH",
          description: `Malformed input "${test.input}" crashes system`,
          mitigation: "Add strict schema validation and try-catch blocks",
        });
      }
    }

    // 2. Race conditions - what if concurrent requests?
    const raceTests = this.generateRaceConditions(system.statefulOps);
    for (const race of raceTests) {
      if (this.detectConflict(race)) {
        vulnerabilities.push({
          type: "RACE_CONDITION",
          severity: "HIGH",
          description: `Concurrent ${race.op1} and ${race.op2} race on shared state`,
          mitigation: "Implement mutex locks or atomic transactions",
        });
      }
    }

    // 3. Resource exhaustion - what if malicious resource requests?
    const exhaustionTests = this.generateExhaustionTests(system.resources);
    for (const test of exhaustionTests) {
      if (test.request > test.quota) {
        vulnerabilities.push({
          type: "RESOURCE_EXHAUSTION",
          severity: "MEDIUM",
          description: `Request for ${test.request} exceeds ${test.resource} quota ${test.quota}`,
          mitigation: "Implement rate limiting and stricter quotas",
        });
      }
    }

    // Final validation of top vulnerabilities
    const highSev = vulnerabilities.filter((v) => v.severity === "HIGH");
    const confirmed: Vulnerability[] = [];

    for (const v of highSev) {
      const approved = await this.twoTower.validateAction({
        action: `confirm_vulnerability:${v.type}`,
        confidence: 0.8,
        risk: "low",
        payload: v,
        requiresValidation: true,
      });
      if (approved) confirmed.push(v);
    }

    return [...confirmed, ...vulnerabilities.filter((v) => v.severity !== "HIGH")].sort(
      (a, b) => this.severityScore(b.severity) - this.severityScore(a.severity),
    );
  }

  async redTeam(system: SystemSpec): Promise<AttackScenario[]> {
    // Simulate attacker mindset
    const vectors: AttackScenario[] = [];

    // Social Engineering
    vectors.push({
      name: "Phishing via Tool Output",
      vector: "Malicious prompt injection in tool output",
      likelihood: 0.7,
      impact: "Exfiltration of session keys",
    });

    // Timing
    vectors.push({
      name: "Timing Side-Channel",
      vector: "Analyzing response time to guess internal state",
      likelihood: 0.3,
      impact: "Information leakage",
    });

    return vectors;
  }

  // --- Helper Methods ---

  private generateFuzzTests(inputs: InputSpec[]) {
    // Real common attack vectors
    const vectors = [
      { name: "XSS", val: "<script>alert(1)</script>" },
      { name: "SQLi", val: "' OR 1=1--" },
      { name: "PathTraversal", val: "../../../etc/passwd" },
      { name: "BufferOverflow", val: "A".repeat(10000) },
    ];

    return inputs.flatMap((i) => vectors.map((v) => ({ input: v.val, vector: v.name, target: i })));
  }

  private simulateInput(test: any) {
    // Heuristic analysis of susceptibility based on type and validation
    const target = test.target as InputSpec;

    // If it's a string input without validation, it's vulnerable
    if (target.type === "string" && !target.validation) {
      return {
        crashed: true,
        behavior: `Potential ${test.vector} vulnerability (Unsanitized Input)`,
      };
    }

    // Check for specific weakness signatures
    if (test.vector === "SQLi" && target.name.toLowerCase().includes("id")) {
      return { crashed: true, behavior: "SQL Injection Susceptibility" };
    }

    return { crashed: false };
  }

  private generateRaceConditions(ops: OperationSpec[]) {
    const pairs = [];
    for (let i = 0; i < ops.length; i++) {
      for (let j = i + 1; j < ops.length; j++) {
        pairs.push({ op1: ops[i].name, op2: ops[j].name, ops: [ops[i], ops[j]] });
      }
    }
    return pairs;
  }

  private detectConflict(race: any) {
    const [op1, op2] = race.ops;
    // Conflict if one writes to what the other reads/writes
    const op1Writes = new Set(op1.writes);
    const op2Reads = new Set(op2.reads);
    const op2Writes = new Set(op2.writes);

    const conflictRw = Array.from(op1Writes).some((w) => op2Reads.has(w as string));
    const conflictWr = Array.from(op2Writes).some((w) => new Set(op1.reads).has(w as string));
    const conflictWw = Array.from(op1Writes).some((w) => op2Writes.has(w as string));

    return conflictRw || conflictWr || conflictWw;
  }

  private generateExhaustionTests(resources: ResourceSpec[]) {
    return resources.map((r) => ({ resource: r.type, quota: r.quota, request: r.quota * 10 }));
  }

  private severityScore(s: string) {
    return s === "HIGH" ? 3 : s === "MEDIUM" ? 2 : 1;
  }
}
