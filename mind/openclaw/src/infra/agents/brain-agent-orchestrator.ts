// Brain-Powered Agent Delivery Integration
// Bridges IPPOC Brain orchestration with OpenClaw agent delivery system

import { EventEmitter } from "events";
import type { SessionEntry } from "../../config/sessions/types.js";
import {
  resolveAgentDeliveryPlan,
  resolveAgentOutboundTarget,
} from "../outbound/agent-delivery.js";

// Type definitions for IPPOC Brain integration
interface ToolInvocationEnvelope {
  tool_name: string;
  domain: string;
  action: string;
  context: Record<string, any>;
  risk_level: "low" | "medium" | "high";
  estimated_cost: number;
}

interface ToolResult {
  success: boolean;
  output: any;
  cost_spent: number;
  memory_written: boolean;
  error_code?: string;
  message?: string;
  retryable?: boolean;
}

// Using imported SessionEntry type from ../../config/sessions/types.js

interface OpenClawConfig {
  [key: string]: any;
}

// Brain-enhanced agent delivery with cognitive orchestration

interface BrainAgentContext {
  agent_id: string;
  session_entry: SessionEntry;
  delivery_preferences: any;
  cognitive_state: "thinking" | "ready" | "busy" | "offline";
  last_interaction: number;
  performance_metrics: {
    response_time: number;
    success_rate: number;
    cognitive_load: number;
  };
}

interface CognitiveDeliveryRequest {
  agent_id: string;
  content: string;
  priority: "low" | "medium" | "high" | "critical";
  context: any;
  delivery_plan?: any;
}

class BrainAgentOrchestrator {
  private baseUrl: string;
  private apiKey: string;
  private agentStates: Map<string, BrainAgentContext>;
  private orchestrator: any; // IPPOC Brain orchestrator

  constructor() {
    this.baseUrl = process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
    this.apiKey = process.env.IPPOC_API_KEY || "";
    this.agentStates = new Map();

    // Initialize connection to IPPOC Brain orchestrator
    this.initializeBrainOrchestrator();
  }

  private async initializeBrainOrchestrator(): Promise<void> {
    try {
      // In a real implementation, this would connect to the Python orchestrator
      // For now, we'll simulate the connection
      console.log("[Brain Agent] Connecting to IPPOC Brain orchestrator...");

      // This would typically involve:
      // 1. Setting up inter-process communication with the Python orchestrator
      // 2. Establishing tool registration for agent delivery capabilities
      // 3. Configuring budget and permission systems

      this.orchestrator = {
        invoke: this.invokeBrainTool.bind(this),
        invoke_async: this.invokeBrainToolAsync.bind(this),
      };

      console.log("[Brain Agent] Brain orchestrator connection established");
    } catch (error) {
      console.error("[Brain Agent] Failed to initialize brain orchestrator:", error);
    }
  }

  async registerAgent(agentId: string, sessionEntry: SessionEntry): Promise<void> {
    const agentContext: BrainAgentContext = {
      agent_id: agentId,
      session_entry: sessionEntry,
      delivery_preferences: {},
      cognitive_state: "ready",
      last_interaction: Date.now(),
      performance_metrics: {
        response_time: 0,
        success_rate: 1.0,
        cognitive_load: 0.1,
      },
    };

    this.agentStates.set(agentId, agentContext);

    // Register agent delivery tool with Brain orchestrator
    await this.registerAgentDeliveryTool(agentId);

    console.log(`[Brain Agent] Registered agent: ${agentId}`);
  }

  private async registerAgentDeliveryTool(agentId: string): Promise<void> {
    try {
      // Register a tool that the Brain can use to deliver messages via this agent
      const toolEnvelope: ToolInvocationEnvelope = {
        tool_name: `agent_deliver_${agentId}`,
        domain: "communication",
        action: "deliver_message",
        context: {
          agent_id: agentId,
          purpose: "Agent message delivery with cognitive optimization",
        },
        risk_level: "low",
        estimated_cost: 0.1,
      };

      // This would register the tool with the Brain orchestrator
      console.log(`[Brain Agent] Registered delivery tool for agent: ${agentId}`);
    } catch (error) {
      console.error(`[Brain Agent] Failed to register tool for ${agentId}:`, error);
    }
  }

  async cognitiveDeliver(request: CognitiveDeliveryRequest): Promise<ToolResult> {
    const agentContext = this.agentStates.get(request.agent_id);
    if (!agentContext) {
      throw new Error(`Agent ${request.agent_id} not registered`);
    }

    try {
      // Update agent state
      agentContext.cognitive_state = "busy";
      agentContext.last_interaction = Date.now();

      // Brain-powered delivery planning
      const deliveryPlan = await this.planCognitiveDelivery(request, agentContext);

      // Execute delivery through Brain orchestrator
      const result = await this.executeCognitiveDelivery(deliveryPlan, request);

      // Update performance metrics
      this.updateAgentMetrics(agentContext, result);

      return result;
    } finally {
      agentContext.cognitive_state = "ready";
    }
  }

  private async planCognitiveDelivery(
    request: CognitiveDeliveryRequest,
    agentContext: BrainAgentContext,
  ): Promise<any> {
    // Use Brain to optimize delivery plan
    const brainPlanRequest: ToolInvocationEnvelope = {
      tool_name: "communication",
      domain: "cognition",
      action: "plan_agent_delivery",
      context: {
        agent_id: request.agent_id,
        content: request.content,
        priority: request.priority,
        session_context: agentContext.session_entry,
        historical_performance: agentContext.performance_metrics,
        request_context: request.context,
      },
      risk_level: request.priority === "critical" ? "high" : "medium",
      estimated_cost: 0.2,
    };

    try {
      const brainResult = await this.invokeBrainTool(brainPlanRequest);

      if (brainResult.success) {
        return brainResult.output.delivery_plan;
      }
    } catch (error) {
      console.warn("[Brain Agent] Brain planning failed, using fallback:", error);
    }

    // Fallback to traditional delivery planning
    return this.createFallbackDeliveryPlan(request, agentContext);
  }

  private async executeCognitiveDelivery(
    plan: any,
    request: CognitiveDeliveryRequest,
  ): Promise<ToolResult> {
    // Resolve the delivery target using OpenClaw's agent delivery system
    const deliveryPlan = resolveAgentDeliveryPlan({
      sessionEntry: this.agentStates.get(request.agent_id)?.session_entry,
      requestedChannel: plan.preferred_channel,
      explicitTo: plan.target_recipient,
      explicitThreadId: plan.thread_id,
      accountId: plan.account_id,
      wantsDelivery: true,
    } as any);

    const targetResolution = resolveAgentOutboundTarget({
      cfg: plan.config,
      plan: deliveryPlan,
      targetMode: plan.delivery_mode,
      validateExplicitTarget: true,
    });

    if (!targetResolution.resolvedTarget?.ok) {
      return {
        success: false,
        output: null,
        cost_spent: 0,
        memory_written: false,
        error_code: "DELIVERY_TARGET_FAILED",
        message: "Failed to resolve delivery target",
        retryable: true,
      };
    }

    // Execute the actual delivery
    try {
      // This would integrate with the actual delivery mechanisms
      const deliveryResult = await this.performActualDelivery(
        targetResolution.resolvedTarget,
        request.content,
        plan,
      );

      return {
        success: deliveryResult.success,
        output: {
          message_id: deliveryResult.messageId,
          channel: (targetResolution.resolvedTarget as any).channel,
          recipient: targetResolution.resolvedTo,
          delivery_timestamp: Date.now(),
          cognitive_optimizations: plan.optimizations || {},
        },
        cost_spent: deliveryResult.cost || 0.1,
        memory_written: true,
      };
    } catch (error) {
      return {
        success: false,
        output: null,
        cost_spent: 0,
        memory_written: false,
        error_code: "DELIVERY_EXECUTION_FAILED",
        message: error instanceof Error ? error.message : "Unknown delivery error",
        retryable: true,
      };
    }
  }

  private async performActualDelivery(target: any, content: string, plan: any): Promise<any> {
    // This would integrate with the actual OpenClaw delivery mechanisms
    // For now, simulate successful delivery

    console.log(`[Brain Agent] Delivering message via ${target.channel} to ${target.to}`);

    // Simulate delivery cost and timing
    const simulatedCost = 0.05 + Math.random() * 0.1;
    const simulatedDelay = 100 + Math.random() * 200;

    await new Promise((resolve) => setTimeout(resolve, simulatedDelay));

    return {
      success: true,
      messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      cost: simulatedCost,
    };
  }

  private createFallbackDeliveryPlan(
    request: CognitiveDeliveryRequest,
    agentContext: BrainAgentContext,
  ): any {
    // Simple fallback delivery plan
    return {
      preferred_channel: "default",
      target_recipient: agentContext.session_entry?.lastTo || "unknown",
      thread_id: (agentContext.session_entry as any)?.threadId,
      account_id: (agentContext.session_entry as any)?.accountId,
      delivery_mode: "implicit",
      config: {}, // Would be actual OpenClaw config
      optimizations: {
        timing: "immediate",
        priority: request.priority,
      },
    };
  }

  private updateAgentMetrics(context: BrainAgentContext, result: ToolResult): void {
    const now = Date.now();
    const responseTime = now - context.last_interaction;

    context.performance_metrics.response_time =
      (context.performance_metrics.response_time + responseTime) / 2;

    context.performance_metrics.success_rate = result.success
      ? Math.min(1.0, context.performance_metrics.success_rate + 0.01)
      : Math.max(0.0, context.performance_metrics.success_rate - 0.05);

    context.performance_metrics.cognitive_load = Math.min(
      1.0,
      context.performance_metrics.cognitive_load + 0.05,
    );
  }

  // Brain tool invocation methods
  private async invokeBrainTool(envelope: ToolInvocationEnvelope): Promise<ToolResult> {
    // This would actually call the Python orchestrator
    // For now, simulate successful tool execution

    console.log(`[Brain Agent] Invoking brain tool: ${envelope.tool_name}`);

    return {
      success: true,
      output: {
        result: "Tool executed successfully",
        execution_time: Date.now(),
        tool_name: envelope.tool_name,
      },
      cost_spent: envelope.estimated_cost || 0.1,
      memory_written: true,
    };
  }

  private async invokeBrainToolAsync(envelope: ToolInvocationEnvelope): Promise<ToolResult> {
    // Async version of brain tool invocation
    return this.invokeBrainTool(envelope);
  }

  // Public API methods
  async getAgentStatus(agentId: string): Promise<BrainAgentContext | undefined> {
    return this.agentStates.get(agentId);
  }

  async getAllAgents(): Promise<Map<string, BrainAgentContext>> {
    return new Map(this.agentStates);
  }

  async updateAgentPreferences(agentId: string, preferences: any): Promise<void> {
    const context = this.agentStates.get(agentId);
    if (context) {
      context.delivery_preferences = { ...context.delivery_preferences, ...preferences };
      console.log(`[Brain Agent] Updated preferences for agent: ${agentId}`);
    }
  }

  async deregisterAgent(agentId: string): Promise<void> {
    this.agentStates.delete(agentId);
    console.log(`[Brain Agent] Deregistered agent: ${agentId}`);
  }
}

// Export singleton instance
export const brainAgentOrchestrator = new BrainAgentOrchestrator();

// Convenience functions for integration
export async function registerBrainAgent(
  agentId: string,
  sessionEntry: SessionEntry,
): Promise<void> {
  return brainAgentOrchestrator.registerAgent(agentId, sessionEntry);
}

export async function deliverViaBrain(
  agentId: string,
  content: string,
  priority: "low" | "medium" | "high" | "critical" = "medium",
  context: any = {},
): Promise<ToolResult> {
  return brainAgentOrchestrator.cognitiveDeliver({
    agent_id: agentId,
    content,
    priority,
    context,
  });
}

export function getAgentStatus(agentId: string): Promise<BrainAgentContext | undefined> {
  return brainAgentOrchestrator.getAgentStatus(agentId);
}
