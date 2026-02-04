import { z } from "zod";
import { getIPPOCAdapter } from "../ippoc-adapter";

export type SignalType = "KERNEL_EVENT" | "USER_INTENT" | "HIVE_PREFIX";

export interface Signal {
  id: string;
  type: SignalType;
  priority: number; // 0-100
  payload: any;
}

export class Thalamus {
  private adapter;
  private habits: Map<string, string>;
  private reflexRules: Array<{ condition: (signal: Signal) => boolean; action: (signal: Signal) => string }>;

  constructor() {
    this.adapter = getIPPOCAdapter();
    this.habits = new Map();
    this.reflexRules = this.initializeReflexRules();
    console.log("[Thalamus] Initialized.");
  }

  /**
   * Route signal based on priority and type
   */
  public async route(signal: Signal): Promise<string> {
    console.log(`[Thalamus] Routing signal ${signal.id} (P:${signal.priority})`);

    // 1. Reflex Path (High Priority / Danger)
    if (signal.priority >= 90) {
      return this.triggerReflex(signal);
    }

    // 2. Habit Path (Cached / Low Risk)
    if (signal.priority < 30) {
      const habitResponse = this.triggerHabit(signal);
      if (habitResponse) {
        return habitResponse;
      }
    }

    // 3. Cognitive Path (LLM Attention Required)
    return await this.triggerCognition(signal);
  }

  /**
   * Initialize reflex rules
   */
  private initializeReflexRules(): Array<{ condition: (signal: Signal) => boolean; action: (signal: Signal) => string }> {
    return [
      {
        condition: (signal) => 
          signal.type === "KERNEL_EVENT" && 
          (signal.payload.error === "OOM_KILL_IMMINENT" || signal.payload.error === "OOM_KILL"),
        action: (signal) => {
          console.warn(`!!! THALAMUS REFLEX: Auto-killing process ${signal.payload.pid} !!!`);
          try {
            process.kill(signal.payload.pid, "SIGKILL");
            return `REFLEX: Auto-killed process ${signal.payload.pid}`;
          } catch (e) {
            console.error("Failed to kill process:", e);
            return "REFLEX: Failed to kill process";
          }
        },
      },
      {
        condition: (signal) => 
          signal.type === "KERNEL_EVENT" && 
          signal.payload.error === "HIGH_CPU_USAGE",
        action: (signal) => {
          console.warn(`!!! THALAMUS REFLEX: Throttling process ${signal.payload.pid} !!!`);
          try {
             // Renice to lower priority (+10)
             // Requires permissions, but this is the intent
             // In a real env, we might wrap this in a sudo-helper or just log it if permission denied
             import("child_process").then(cp => {
                 cp.exec(`renice +10 -p ${signal.payload.pid}`);
             });
             return `REFLEX: Throttled process ${signal.payload.pid} (renice +10)`;
          } catch (e) {
             return "REFLEX: Failed to throttle";
          }
        },
      },
      {
        condition: (signal) => 
          signal.type === "HIVE_PREFIX" && 
          signal.payload.action === "SHUTDOWN",
        action: (signal) => {
          console.warn(`!!! THALAMUS REFLEX: Initiating shutdown !!!`);
          if (signal.payload.force) {
              process.exit(1);
          }
          setTimeout(() => process.exit(0), 1000); // Graceful shutdown
          return `REFLEX: System shutdown initiated`;
        },
      },
    ];
  }

  /**
   * Trigger reflex action based on signal
   */
  private triggerReflex(signal: Signal): string {
    const applicableRule = this.reflexRules.find(rule => rule.condition(signal));
    
    if (applicableRule) {
      return applicableRule.action(signal);
    } else {
      console.warn("!!! THALAMUS REFLEX: No specific reflex rule found !!!");
      return "REFLEX: Default action taken";
    }
  }

  /**
   * Trigger habit response if available
   */
  private triggerHabit(signal: Signal): string | null {
    const query = this.extractQuery(signal);
    if (query && this.habits.has(query)) {
      console.log(`[Thalamus] Habit response for query: ${query}`);
      return `HABIT: ${this.habits.get(query)}`;
    }
    return null;
  }

  /**
   * Extract query from signal
   */
  private extractQuery(signal: Signal): string | null {
    if (signal.type === "USER_INTENT" && signal.payload.query) {
      return signal.payload.query.toLowerCase().trim();
    }
    return null;
  }

  /**
   * Trigger cognitive processing
   */
  /**
   * Trigger cognitive processing via IPPOC Brain (Cerebellum)
   */
  private async triggerCognition(signal: Signal): Promise<string> {
    console.log("[Thalamus] Routing cognition via IPPOC Orchestrator...");

    const prompt = `Signal ${signal.type} (priority ${signal.priority}): ${JSON.stringify(signal.payload)}`;
    try {
      const response = await this.adapter.runReasoning(prompt);
      return response ? `COGNITIVE: ${response}` : "COGNITIVE: No response from Brain";
    } catch (e) {
      console.error("[Thalamus] Orchestrator reasoning failed:", e);
      return "COGNITIVE: Brain unavailable (Orchestrator Error)";
    }
  }

  /**
   * Add habit to the system
   */
  public addHabit(query: string, response: string): void {
    this.habits.set(query.toLowerCase().trim(), response);
    console.log(`[Thalamus] Habit added: ${query}`);
  }

  /**
   * Remove habit from the system
   */
  public removeHabit(query: string): boolean {
    return this.habits.delete(query.toLowerCase().trim());
  }

  /**
   * Get all habits
   */
  public getHabits(): Array<{ query: string; response: string }> {
    return Array.from(this.habits.entries()).map(([query, response]) => ({
      query,
      response,
    }));
  }
}
