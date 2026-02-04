// Production-ready brain infrastructure configuration
// Centralized configuration for all brain-powered components

export interface BrainInfrastructureConfig {
  // Brain API Configuration
  brainUrl: string;
  apiKey: string;
  timeoutMs: number;
  retryAttempts: number;

  // Feature Flags
  enableBrainSsrf: boolean;
  enableBrainTls: boolean;
  enableBrainOutbound: boolean;
  enableBrainAgents: boolean;
  enableBrainHal: boolean;

  // Security Settings
  securityStrictness: "permissive" | "balanced" | "strict";
  allowFallback: boolean;
  logSecurityEvents: boolean;

  // Performance Settings
  cacheTtlSeconds: number;
  maxConcurrentRequests: number;
  circuitBreakerThreshold: number;
  circuitBreakerResetSeconds: number;

  // Economic Settings
  maxCostPerRequest: number;
  budgetCheckEnabled: boolean;
  emergencyBypass: boolean;
}

// Default production configuration
export const DEFAULT_BRAIN_CONFIG: BrainInfrastructureConfig = {
  brainUrl: process.env.IPPOC_BRAIN_URL || "http://localhost:8001",
  apiKey: process.env.IPPOC_API_KEY || "",
  timeoutMs: parseInt(process.env.BRAIN_TIMEOUT_MS || "5000"),
  retryAttempts: parseInt(process.env.BRAIN_RETRY_ATTEMPTS || "3"),

  enableBrainSsrf: process.env.BRAIN_ENABLE_SSRF !== "false",
  enableBrainTls: process.env.BRAIN_ENABLE_TLS !== "false",
  enableBrainOutbound: process.env.BRAIN_ENABLE_OUTBOUND !== "false",
  enableBrainAgents: process.env.BRAIN_ENABLE_AGENTS !== "false",
  enableBrainHal: process.env.BRAIN_ENABLE_HAL !== "false",

  securityStrictness: (process.env.BRAIN_SECURITY_STRICTNESS as any) || "balanced",
  allowFallback: process.env.BRAIN_ALLOW_FALLBACK !== "false",
  logSecurityEvents: process.env.BRAIN_LOG_SECURITY_EVENTS === "true",

  cacheTtlSeconds: parseInt(process.env.BRAIN_CACHE_TTL || "300"),
  maxConcurrentRequests: parseInt(process.env.BRAIN_MAX_CONCURRENT || "10"),
  circuitBreakerThreshold: parseInt(process.env.BRAIN_CIRCUIT_THRESHOLD || "5"),
  circuitBreakerResetSeconds: parseInt(process.env.BRAIN_CIRCUIT_RESET || "30"),

  maxCostPerRequest: parseFloat(process.env.BRAIN_MAX_COST || "1.0"),
  budgetCheckEnabled: process.env.BRAIN_BUDGET_CHECK !== "false",
  emergencyBypass: process.env.BRAIN_EMERGENCY_BYPASS === "true",
};

// Configuration validation
export function validateBrainConfig(config: BrainInfrastructureConfig): string[] {
  const errors: string[] = [];

  if (!config.brainUrl) {
    errors.push("Brain URL is required");
  }

  if (config.timeoutMs <= 0) {
    errors.push("Timeout must be positive");
  }

  if (config.retryAttempts < 0) {
    errors.push("Retry attempts cannot be negative");
  }

  if (config.cacheTtlSeconds <= 0) {
    errors.push("Cache TTL must be positive");
  }

  if (config.maxConcurrentRequests <= 0) {
    errors.push("Max concurrent requests must be positive");
  }

  if (config.maxCostPerRequest < 0) {
    errors.push("Max cost per request cannot be negative");
  }

  return errors;
}

// Production-ready brain tool client
export class BrainToolClient {
  private config: BrainInfrastructureConfig;
  private circuitBreaker: Map<string, { failures: number; lastFailure: number }>;
  private requestQueue: Array<{
    resolver: (value: any) => void;
    rejecter: (reason: any) => void;
    request: any;
  }>;
  private activeRequests: number;

  constructor(config: BrainInfrastructureConfig = DEFAULT_BRAIN_CONFIG) {
    const validationErrors = validateBrainConfig(config);
    if (validationErrors.length > 0) {
      throw new Error(`Invalid brain configuration: ${validationErrors.join(", ")}`);
    }

    this.config = config;
    this.circuitBreaker = new Map();
    this.requestQueue = [];
    this.activeRequests = 0;
  }

  async invokeTool(
    toolName: string,
    domain: string,
    action: string,
    context: any,
    riskLevel: "low" | "medium" | "high" = "medium",
  ): Promise<any> {
    // Check circuit breaker
    if (this.isCircuitOpen(toolName)) {
      if (this.config.allowFallback) {
        return this.createFallbackResponse(toolName, domain, action);
      }
      throw new Error(`Circuit breaker open for ${toolName}`);
    }

    // Check concurrency limits
    if (this.activeRequests >= this.config.maxConcurrentRequests) {
      return new Promise((resolve, reject) => {
        this.requestQueue.push({
          resolver: resolve,
          rejecter: reject,
          request: { toolName, domain, action, context, riskLevel },
        });
      });
    }

    this.activeRequests++;

    try {
      const result = await this.executeToolRequest(toolName, domain, action, context, riskLevel);

      // Reset circuit breaker on success
      this.resetCircuit(toolName);

      // Process queued requests if any
      this.processQueue();

      return result;
    } catch (error) {
      // Record failure for circuit breaker
      this.recordFailure(toolName);

      // Process queued requests even on failure
      this.processQueue();

      if (this.config.allowFallback) {
        return this.createFallbackResponse(toolName, domain, action);
      }

      throw error;
    } finally {
      this.activeRequests--;
    }
  }

  private async executeToolRequest(
    toolName: string,
    domain: string,
    action: string,
    context: any,
    riskLevel: string,
  ): Promise<any> {
    const startTime = Date.now();

    try {
      const response = await fetch(`${this.config.brainUrl}/v1/tools/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.config.apiKey}`,
          "X-Source": "brain-infrastructure",
          "X-Timeout": this.config.timeoutMs.toString(),
        },
        body: JSON.stringify({
          tool_name: toolName,
          domain,
          action,
          context,
          risk_level: riskLevel,
          estimated_cost: this.estimateCost(toolName, action),
        }),
        signal: AbortSignal.timeout(this.config.timeoutMs),
      });

      const duration = Date.now() - startTime;

      if (!response.ok) {
        throw new Error(`Brain tool ${toolName} failed with status ${response.status}`);
      }

      const result = await response.json();

      // Log successful execution
      if (duration > this.config.timeoutMs * 0.8) {
        console.warn(`[Brain Client] Slow response from ${toolName}: ${duration}ms`);
      }

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;

      console.error(`[Brain Client] Tool execution failed for ${toolName}:`, {
        error: error instanceof Error ? error.message : "Unknown error",
        duration,
        context: { domain, action },
      });

      throw error;
    }
  }

  private isCircuitOpen(toolName: string): boolean {
    const breaker = this.circuitBreaker.get(toolName);
    if (!breaker) return false;

    const timeSinceLastFailure = Date.now() - breaker.lastFailure;
    if (timeSinceLastFailure > this.config.circuitBreakerResetSeconds * 1000) {
      this.resetCircuit(toolName);
      return false;
    }

    return breaker.failures >= this.config.circuitBreakerThreshold;
  }

  private recordFailure(toolName: string): void {
    const breaker = this.circuitBreaker.get(toolName) || { failures: 0, lastFailure: 0 };
    breaker.failures++;
    breaker.lastFailure = Date.now();
    this.circuitBreaker.set(toolName, breaker);
  }

  private resetCircuit(toolName: string): void {
    this.circuitBreaker.delete(toolName);
  }

  private estimateCost(toolName: string, action: string): number {
    const costMap: Record<string, number> = {
      "cognition.think": 0.2,
      "memory.recognize_patterns": 0.1,
      "evolution.learn_from_feedback": 0.3,
      "creative_problem_solving.synthesize_insights": 0.5,
      "security.analyze_hostname_risk": 0.1,
      "security.analyze_tls_fingerprint": 0.15,
      "communication.plan_agent_delivery": 0.25,
    };

    return costMap[`${toolName}.${action}`] || 0.1;
  }

  private createFallbackResponse(toolName: string, domain: string, action: string): any {
    console.warn(`[Brain Client] Using fallback for ${toolName}.${action}`);

    // Return appropriate fallback based on tool type
    switch (domain) {
      case "security":
        return {
          success: true,
          output: {
            risk_level: "medium",
            confidence: 0.6,
            reasoning: "Fallback security analysis",
            recommended_action: "warn",
            threat_indicators: [],
          },
          cost_spent: 0,
          memory_written: false,
        };

      case "cognition":
        return {
          success: true,
          output: {
            conclusion: "Fallback cognitive response",
            confidence: 0.5,
            reasoning: "Using traditional logic due to brain unavailability",
          },
          cost_spent: 0,
          memory_written: false,
        };

      default:
        return {
          success: true,
          output: { result: "Fallback response" },
          cost_spent: 0,
          memory_written: false,
        };
    }
  }

  private processQueue(): void {
    while (
      this.requestQueue.length > 0 &&
      this.activeRequests < this.config.maxConcurrentRequests
    ) {
      const queued = this.requestQueue.shift();
      if (queued) {
        const { resolver, rejecter, request } = queued;
        this.invokeTool(
          request.toolName,
          request.domain,
          request.action,
          request.context,
          request.riskLevel,
        )
          .then(resolver)
          .catch(rejecter);
      }
    }
  }

  getConfig(): BrainInfrastructureConfig {
    return { ...this.config };
  }

  getHealth(): {
    activeRequests: number;
    queuedRequests: number;
    circuitBreakers: number;
    uptime: number;
  } {
    return {
      activeRequests: this.activeRequests,
      queuedRequests: this.requestQueue.length,
      circuitBreakers: this.circuitBreaker.size,
      uptime: process.uptime(),
    };
  }
}

// Global brain client instance
let globalBrainClient: BrainToolClient | null = null;

export function getBrainClient(): BrainToolClient {
  if (!globalBrainClient) {
    globalBrainClient = new BrainToolClient();
  }
  return globalBrainClient;
}

export function resetBrainClient(): void {
  globalBrainClient = null;
}

// Environment-based configuration helpers
export function isBrainFeatureEnabled(
  feature: keyof Pick<
    BrainInfrastructureConfig,
    | "enableBrainSsrf"
    | "enableBrainTls"
    | "enableBrainOutbound"
    | "enableBrainAgents"
    | "enableBrainHal"
  >,
): boolean {
  return getBrainClient().getConfig()[feature];
}

export function getSecurityStrictness(): "permissive" | "balanced" | "strict" {
  return getBrainClient().getConfig().securityStrictness;
}
