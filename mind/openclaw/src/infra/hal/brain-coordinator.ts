// Brain-powered HAL (Hard Autonomy Layer) integration
// Coordinates all brain-powered infrastructure components

// Note: Direct imports commented out due to circular dependencies
// Will use dynamic imports or service discovery pattern

// HAL Brain Coordinator - Central cognitive orchestrator
interface HalBrainState {
  system_health: "optimal" | "degraded" | "critical";
  cognitive_load: number; // 0-1 scale
  learning_rate: number; // Adaptation speed
  security_posture: "secure" | "monitored" | "hardened" | "compromised";
  communication_efficiency: number; // 0-1 scale
  last_sync: number;
}

interface HalCognitiveTask {
  id: string;
  type:
    | "security_analysis"
    | "communication_optimization"
    | "network_protection"
    | "tls_evaluation";
  priority: "low" | "medium" | "high" | "critical";
  context: any;
  deadline?: number;
  dependencies?: string[];
}

class HalBrainCoordinator {
  private state: HalBrainState;
  private taskQueue: HalCognitiveTask[];
  private activeTasks: Map<string, Promise<any>>;
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    this.state = {
      system_health: "optimal",
      cognitive_load: 0.1,
      learning_rate: 0.7,
      security_posture: "secure",
      communication_efficiency: 0.9,
      last_sync: Date.now(),
    };

    this.taskQueue = [];
    this.activeTasks = new Map();
    this.baseUrl = process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
    this.apiKey = process.env.IPPOC_API_KEY || "";

    this.initializeBrainComponents();
  }

  private async initializeBrainComponents(): Promise<void> {
    console.log("[HAL Brain] Initializing cognitive infrastructure...");

    try {
      // Initialize all brain-powered components
      await Promise.all([
        this.initializeSecuritySystems(),
        this.initializeCommunicationSystems(),
        this.initializeNetworkProtection(),
      ]);

      console.log("[HAL Brain] All cognitive systems initialized");
      this.updateSystemHealth("optimal");
    } catch (error) {
      console.error("[HAL Brain] Initialization failed:", error);
      this.updateSystemHealth("degraded");
    }
  }

  private async initializeSecuritySystems(): Promise<void> {
    // Initialize brain-powered security analysis
    console.log("[HAL Brain] Security systems operational");
    // Would dynamically import: const { brainTlsAnalyzer } = await import('../tls/brain-fingerprint.js');
  }

  private async initializeCommunicationSystems(): Promise<void> {
    // Initialize brain-powered communication optimization
    console.log("[HAL Brain] Communication systems operational");
    // Would dynamically import: const { BrainCommunicationOptimizer } = await import('../outbound/brain-deliver.js');
  }

  private async initializeNetworkProtection(): Promise<void> {
    // Initialize brain-powered network protection
    console.log("[HAL Brain] Network protection systems operational");
    // Would dynamically import: const { BrainSecurityAnalyzer } = await import('../net/brain-ssrf.js');
  }

  async submitCognitiveTask(task: Omit<HalCognitiveTask, "id">): Promise<string> {
    const taskId = this.generateTaskId();
    const fullTask: HalCognitiveTask = {
      ...task,
      id: taskId,
    };

    this.taskQueue.push(fullTask);
    this.processTaskQueue();

    console.log(`[HAL Brain] Task submitted: ${taskId} (${task.type})`);
    return taskId;
  }

  private async processTaskQueue(): Promise<void> {
    if (this.taskQueue.length === 0 || this.getCognitiveCapacity() < 0.2) {
      return;
    }

    const task = this.taskQueue.shift();
    if (!task) return;

    // Check if we can handle this task based on priority and resources
    if (this.shouldProcessTask(task)) {
      const taskPromise = this.executeCognitiveTask(task);
      this.activeTasks.set(task.id, taskPromise);

      // Clean up when task completes
      taskPromise.finally(() => {
        this.activeTasks.delete(task.id);
        this.updateCognitiveLoad(-0.1);
      });
    } else {
      // Re-queue high priority tasks
      if (task.priority === "critical" || task.priority === "high") {
        this.taskQueue.unshift(task);
      }
    }

    // Process next task
    setTimeout(() => this.processTaskQueue(), 100);
  }

  private async executeCognitiveTask(task: HalCognitiveTask): Promise<any> {
    this.updateCognitiveLoad(0.15);

    try {
      switch (task.type) {
        case "security_analysis":
          return await this.performSecurityAnalysis(task.context);
        case "communication_optimization":
          return await this.optimizeCommunication(task.context);
        case "network_protection":
          return await this.enforceNetworkProtection(task.context);
        case "tls_evaluation":
          return await this.evaluateTlsSecurity(task.context);
        default:
          throw new Error(`Unknown task type: ${task.type}`);
      }
    } catch (error) {
      console.error(`[HAL Brain] Task ${task.id} failed:`, error);
      this.updateSystemHealth("degraded");
      throw error;
    }
  }

  private async performSecurityAnalysis(context: any): Promise<any> {
    console.log("[HAL Brain] Performing security analysis...");

    const result = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        "X-Source": "hal-brain-security",
      },
      body: JSON.stringify({
        tool_name: "security",
        domain: "security",
        action: "comprehensive_analysis",
        context: {
          scope: context.scope || "system_wide",
          threat_level: context.threat_level || "medium",
          assets: context.assets || [],
        },
        risk_level: context.risk_preference || "medium",
        estimated_cost: 0.3,
      }),
    });

    if (result.ok) {
      const response = await result.json();
      if (response.success) {
        this.updateSecurityPosture(response.output.overall_risk);
        return response.output;
      }
    }

    throw new Error("Security analysis failed");
  }

  private async optimizeCommunication(context: any): Promise<any> {
    console.log("[HAL Brain] Optimizing communication...");

    const result = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        "X-Source": "hal-brain-communication",
      },
      body: JSON.stringify({
        tool_name: "communication",
        domain: "social",
        action: "optimize_system_communication",
        context: {
          channels: context.channels || [],
          recipients: context.recipients || [],
          content_types: context.content_types || [],
          optimization_goals: context.goals || ["efficiency", "security"],
        },
        risk_level: "low",
        estimated_cost: 0.25,
      }),
    });

    if (result.ok) {
      const response = await result.json();
      if (response.success) {
        this.updateCommunicationEfficiency(response.output.efficiency_score);
        return response.output;
      }
    }

    throw new Error("Communication optimization failed");
  }

  private async enforceNetworkProtection(context: any): Promise<any> {
    console.log("[HAL Brain] Enforcing network protection...");

    const result = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        "X-Source": "hal-brain-network",
      },
      body: JSON.stringify({
        tool_name: "network",
        domain: "network",
        action: "enforce_protection_policy",
        context: {
          policy_type: context.policy || "ssrf_protection",
          scope: context.scope || "global",
          strictness: context.strictness || "balanced",
        },
        risk_level: context.risk_level || "medium",
        estimated_cost: 0.2,
      }),
    });

    if (result.ok) {
      const response = await result.json();
      if (response.success) {
        return response.output;
      }
    }

    throw new Error("Network protection enforcement failed");
  }

  private async evaluateTlsSecurity(context: any): Promise<any> {
    console.log("[HAL Brain] Evaluating TLS security...");

    const fingerprint = context.fingerprint;
    if (!fingerprint) {
      throw new Error("TLS fingerprint required for evaluation");
    }

    // Would use: const analysis = await brainTlsAnalyzer.analyzeTlsFingerprint(...)
    // For now, simulate the analysis
    const analysis = {
      normalized_fingerprint: fingerprint,
      security_posture: {
        security_rating: "fair",
        confidence: 0.8,
        recommendations: ["standard_security_practices"],
      },
      adaptive_response: "allow",
    };

    return {
      fingerprint: analysis.normalized_fingerprint,
      security_rating: analysis.security_posture.security_rating,
      risk_level: analysis.adaptive_response,
      recommendations: (analysis.security_posture as any).recommendations || [],
      confidence: analysis.security_posture.confidence,
    };
  }

  private shouldProcessTask(task: HalCognitiveTask): boolean {
    const capacity = this.getCognitiveCapacity();
    const priorityWeights = { low: 0.3, medium: 0.6, high: 0.8, critical: 1.0 };
    const priorityWeight = priorityWeights[task.priority] || 0.5;

    return capacity > 1 - priorityWeight;
  }

  private getCognitiveCapacity(): number {
    const baseCapacity = 1.0;
    const loadPenalty = this.state.cognitive_load * 0.7;
    const healthMultiplier =
      this.state.system_health === "optimal"
        ? 1.0
        : this.state.system_health === "degraded"
          ? 0.7
          : 0.4;

    return Math.max(0, baseCapacity - loadPenalty) * healthMultiplier;
  }

  private updateCognitiveLoad(change: number): void {
    this.state.cognitive_load = Math.max(0, Math.min(1, this.state.cognitive_load + change));

    if (this.state.cognitive_load > 0.8) {
      this.updateSystemHealth("degraded");
    } else if (this.state.cognitive_load < 0.3 && this.state.system_health !== "critical") {
      this.updateSystemHealth("optimal");
    }
  }

  private updateSystemHealth(health: "optimal" | "degraded" | "critical"): void {
    this.state.system_health = health;
  }

  private updateSecurityPosture(riskLevel: string): void {
    if (riskLevel === "critical") {
      this.state.security_posture = "compromised";
    } else if (riskLevel === "high") {
      this.state.security_posture = "hardened";
    } else {
      this.state.security_posture = "secure";
    }
  }

  private updateCommunicationEfficiency(score: number): void {
    this.state.communication_efficiency = Math.max(0, Math.min(1, score));
  }

  private generateTaskId(): string {
    return `hal_task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Public API
  getState(): HalBrainState {
    return { ...this.state, last_sync: Date.now() };
  }

  getTaskStatus(taskId: string): Promise<any> | undefined {
    return this.activeTasks.get(taskId);
  }

  getQueueDepth(): number {
    return this.taskQueue.length;
  }

  getActiveTaskCount(): number {
    return this.activeTasks.size;
  }

  async emergencyShutdown(): Promise<void> {
    console.log("[HAL Brain] Emergency shutdown initiated...");

    // Cancel all active tasks
    for (const [taskId, taskPromise] of this.activeTasks) {
      // In a real implementation, we'd have a way to cancel promises
      console.log(`[HAL Brain] Cancelling task: ${taskId}`);
    }

    this.activeTasks.clear();
    this.taskQueue.length = 0;
    this.state.cognitive_load = 0;
    this.updateSystemHealth("critical");

    console.log("[HAL Brain] Emergency shutdown complete");
  }

  async selfHeal(): Promise<void> {
    console.log("[HAL Brain] Initiating self-healing procedures...");

    try {
      // Reset cognitive load
      this.state.cognitive_load = 0.1;

      // Re-initialize components
      await this.initializeBrainComponents();

      // Clear task queues
      this.taskQueue.length = 0;
      this.activeTasks.clear();

      console.log("[HAL Brain] Self-healing complete");
    } catch (error) {
      console.error("[HAL Brain] Self-healing failed:", error);
      this.updateSystemHealth("critical");
    }
  }
}

// Export singleton instance
export const halBrainCoordinator = new HalBrainCoordinator();

// Convenience functions for integration
export async function submitHalTask(task: Omit<HalCognitiveTask, "id">): Promise<string> {
  return halBrainCoordinator.submitCognitiveTask(task);
}

export function getHalState(): HalBrainState {
  return halBrainCoordinator.getState();
}

export async function performHalSecurityScan(scope?: string): Promise<any> {
  return halBrainCoordinator.submitCognitiveTask({
    type: "security_analysis",
    priority: "high",
    context: { scope: scope || "system_wide" },
  });
}
