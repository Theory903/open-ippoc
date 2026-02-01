import { z } from "zod";

export type SignalType = "KERNEL_EVENT" | "USER_INTENT" | "HIVE_PREFIX";

export interface Signal {
  id: string;
  type: SignalType;
  priority: number; // 0-100
  payload: any;
}

export class Thalamus {
  constructor() {
    console.log("[Thalamus] Initialized.");
  }

  public async route(signal: Signal): Promise<string> {
    console.log(`[Thalamus] Routing signal ${signal.id} (P:${signal.priority})`);

    // 1. Reflex Path (High Priority / Danger)
    if (signal.priority >= 90) {
      return this.triggerReflex(signal);
    }

    // 2. Habit Path (Cached / Low Risk)
    if (signal.priority < 30) {
      return "ROUTED_TO_HABIT"; 
    }

    // 3. Cognitive Path (LLM Attention Required)
    return this.triggerCognition(signal);
  }

  private triggerReflex(signal: Signal): string {
    console.warn("!!! THALAMUS REFLEX TRIGGERED !!!");
    // e.g., Auto-kill process, block IP
    return "REFLEX_ACTION_TAKEN";
  }

  private async triggerCognition(signal: Signal): Promise<string> {
    console.log("[Thalamus] Upstreaming to Cortex for reasoning...");
    return "ROUTED_TO_CORTEX";
  }
}
