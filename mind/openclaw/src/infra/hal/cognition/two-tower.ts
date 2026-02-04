import { getIPPOCAdapter } from "../../../../../../brain/cortex/openclaw-cortex/src/ippoc-adapter.js"; // Keeping .js as NodeNext usually requires it, but verified path.

interface ActionCandidate {
  action: string;
  confidence: number;
  risk: "low" | "medium" | "high" | "critical";
  payload: any;
  requiresValidation: boolean;
}

export class TwoTowerEngine {
  private adapter = getIPPOCAdapter();

  // Tower A: Fast, Cheap, Heuristic/Small Model
  async generateImpulse(context: string): Promise<ActionCandidate> {
    // In a full implementation, this calls a smaller model or uses heuristics
    // For now, we use the adapter's reasoning but ask for JSON (Fast Path)
    const prompt = `
      You are Tower A (Impulse). Propose the NEXT BEST ACTION based on:
      Context: ${context}
      Return JSON: { "action": "snake_case", "risk": "low|medium|high", "thought": "..." }
    `;

    // We treat 'runReasoning' as a generic thinking call.
    // Optimization: We could add specific 'model' param to adapter later.
    const response = await this.adapter.runReasoning(prompt);

    try {
      const data = JSON.parse(this.extractJson(response));
      return {
        action: data.action || "unknown",
        confidence: data.risk === "low" ? 0.8 : 0.6,
        risk: data.risk || "medium",
        payload: { thought: data.thought },
        requiresValidation: this.isHighRisk(data.risk),
      };
    } catch (e) {
      console.warn("[HAL:TwoTower] Failed to parse impulse:", e);
      return {
        action: "error_fallback",
        confidence: 0,
        risk: "low",
        payload: {},
        requiresValidation: false,
      };
    }
  }

  // Tower B: Slow, Deliberate, Reasoning Model
  async validateAction(candidate: ActionCandidate): Promise<boolean> {
    if (!candidate.requiresValidation) return true;

    const prompt = `
      You are Tower B (Validator).
      Proposed Action: ${candidate.action}
      Risk: ${candidate.risk}
      Details: ${JSON.stringify(candidate.payload)}
      
      Should this be executed? RETURN ONLY "YES" or "NO".
    `;

    const decision = await this.adapter.runReasoning(prompt);
    const approved = decision.trim().toUpperCase().startsWith("YES");

    // Log pattern for future training (Pattern Engine)
    await this.logPattern(candidate, decision, approved);

    return approved;
  }

  private isHighRisk(risk: string): boolean {
    return ["medium", "high", "critical"].includes(risk);
  }

  private extractJson(text: string): string {
    const match = text.match(/```json([\s\S]*?)```/);
    return match ? match[1] : text;
  }

  private async logPattern(candidate: ActionCandidate, response: string, approved: boolean) {
    // In Python version this writes to JSONL.
    // Here we store as a 'Fact' in HIDB via adapter for analysis.
    await this.adapter.storeFact(
      `Pattern Log: Action ${candidate.action} (Risk: ${candidate.risk}) was ${approved ? "APPROVED" : "REJECTED"}. Validator thought: ${response}`,
    );
  }
}
