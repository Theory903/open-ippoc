import type { ReplyPayload } from "../../auto-reply/types.js";
import type { ChannelOutboundAdapter } from "../../channels/plugins/types.js";
import type { OpenClawConfig } from "../../config/config.js";
import type { NormalizedOutboundPayload } from "../outbound/payloads.js";
import type { OutboundChannel } from "../outbound/targets.js";
import { loadChannelOutboundAdapter } from "../../channels/plugins/outbound/load.js";

// Brain-powered outbound delivery with cognitive optimization

interface BrainCommunicationAnalysis {
  optimal_channel: string;
  timing_recommendation: "immediate" | "delayed" | "scheduled";
  content_adaptation: string;
  audience_analysis: any;
  risk_assessment: "low" | "medium" | "high";
  confidence: number;
}

interface BrainDeliveryOptimization {
  chunking_strategy: "paragraph" | "sentence" | "thematic";
  tone_adjustment: string;
  personalization_level: number;
  urgency_modulation: number;
}

class BrainCommunicationOptimizer {
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    this.baseUrl = process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
    this.apiKey = process.env.IPPOC_API_KEY || "";
  }

  async analyzeCommunicationContext(params: {
    recipient: string;
    channel: string;
    content: string;
    context?: any;
  }): Promise<BrainCommunicationAnalysis> {
    try {
      const response = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
          "X-Source": "brain-outbound-optimizer",
        },
        body: JSON.stringify({
          tool_name: "communication",
          domain: "social",
          action: "analyze_delivery_context",
          context: {
            recipient: params.recipient,
            channel: params.channel,
            content: params.content,
            additional_context: params.context || {},
          },
          risk_level: "low",
          estimated_cost: 0.2,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.output) {
          return result.output as BrainCommunicationAnalysis;
        }
      }
    } catch (error) {
      console.warn("[Brain Outbound] Communication analysis failed:", error);
    }

    // Fallback analysis
    return this.fallbackAnalysis(params);
  }

  async optimizeDelivery(
    content: string,
    analysis: BrainCommunicationAnalysis,
  ): Promise<BrainDeliveryOptimization> {
    try {
      const response = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
          "X-Source": "brain-outbound-optimizer",
        },
        body: JSON.stringify({
          tool_name: "creative_problem_solving",
          domain: "cognition",
          action: "optimize_communication_delivery",
          context: {
            content,
            communication_analysis: analysis,
            optimization_goals: ["clarity", "engagement", "appropriateness"],
          },
          risk_level: "low",
          estimated_cost: 0.3,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.output) {
          return result.output as BrainDeliveryOptimization;
        }
      }
    } catch (error) {
      console.warn("[Brain Outbound] Delivery optimization failed:", error);
    }

    // Fallback optimization
    return {
      chunking_strategy: "paragraph",
      tone_adjustment: "professional",
      personalization_level: 0.7,
      urgency_modulation: 1.0,
    };
  }

  private fallbackAnalysis(params: {
    recipient: string;
    channel: string;
    content: string;
  }): BrainCommunicationAnalysis {
    // Simple heuristic-based analysis
    const contentLength = params.content.length;
    const hasUrgentWords = /\b(urgent|asap|immediately|now)\b/i.test(params.content);
    const hasQuestion = params.content.includes("?");

    return {
      optimal_channel: params.channel,
      timing_recommendation: hasUrgentWords ? "immediate" : "delayed",
      content_adaptation: hasQuestion ? "interactive" : "informative",
      audience_analysis: { recipient_type: "general" },
      risk_assessment: "low",
      confidence: 0.6,
    };
  }
}

const brainOptimizer = new BrainCommunicationOptimizer();

export interface BrainOutboundDeliveryResult {
  channel: Exclude<OutboundChannel, "none">;
  messageId: string;
  brainOptimizations: {
    analysis: BrainCommunicationAnalysis;
    optimizations: BrainDeliveryOptimization;
  };
  timestamp: number;
  cost: number;
}

type OutboundSendDeps = any; // Simplified for this example

export async function deliverWithBrainOptimization(params: {
  cfg: OpenClawConfig;
  channel: Exclude<OutboundChannel, "none">;
  to: string;
  payloads: ReplyPayload[];
  deps?: OutboundSendDeps;
  context?: any;
}): Promise<BrainOutboundDeliveryResult[]> {
  const results: BrainOutboundDeliveryResult[] = [];

  for (const payload of params.payloads) {
    if (!payload.text) continue;

    try {
      // Brain-powered communication analysis
      const analysis = await brainOptimizer.analyzeCommunicationContext({
        recipient: params.to,
        channel: params.channel,
        content: payload.text,
        context: params.context,
      });

      // Brain-powered delivery optimization
      const optimizations = await brainOptimizer.optimizeDelivery(payload.text, analysis);

      // Apply brain recommendations
      const adaptedContent = applyBrainOptimizations(payload.text, optimizations);

      // Use traditional delivery with brain enhancements
      const channelHandler = await createOptimizedChannelHandler({
        cfg: params.cfg,
        channel: analysis.optimal_channel as OutboundChannel,
        to: params.to,
        deps: params.deps,
        brainOptimizations: optimizations,
      });

      const deliveryResult = await channelHandler.sendText(adaptedContent);

      results.push({
        channel: analysis.optimal_channel as OutboundChannel,
        messageId: deliveryResult.messageId,
        brainOptimizations: {
          analysis,
          optimizations,
        },
        timestamp: Date.now(),
        cost: (deliveryResult.meta as any)?.cost || 0,
      });

      console.log(`[Brain Outbound] Delivered with optimizations:`, {
        channel: analysis.optimal_channel,
        confidence: analysis.confidence,
        adaptations: Object.keys(optimizations).length,
      });
    } catch (error) {
      console.error(`[Brain Outbound] Failed to deliver to ${params.to}:`, error);
      // Could implement fallback delivery here
    }
  }

  return results;
}

function applyBrainOptimizations(
  content: string,
  optimizations: BrainDeliveryOptimization,
): string {
  let adaptedContent = content;

  // Apply tone adjustment
  if (optimizations.tone_adjustment !== "neutral") {
    adaptedContent = `[Tone: ${optimizations.tone_adjustment}] ${adaptedContent}`;
  }

  // Apply personalization
  if (optimizations.personalization_level > 0.8) {
    adaptedContent = `Personalized for you: ${adaptedContent}`;
  }

  // Apply urgency modulation
  if (optimizations.urgency_modulation > 1.2) {
    adaptedContent = `🚨 URGENT: ${adaptedContent}`;
  } else if (optimizations.urgency_modulation < 0.8) {
    adaptedContent = `FYI: ${adaptedContent}`;
  }

  return adaptedContent;
}

async function createOptimizedChannelHandler(params: {
  cfg: OpenClawConfig;
  channel: OutboundChannel;
  to: string;
  deps?: OutboundSendDeps;
  brainOptimizations: BrainDeliveryOptimization;
}) {
  const outbound = await loadChannelOutboundAdapter(params.channel);
  if (!outbound?.sendText) {
    throw new Error(`Outbound not configured for channel: ${params.channel}`);
  }

  return {
    sendText: async (text: string) => {
      // Apply brain chunking strategy
      const chunks = chunkByStrategy(text, params.brainOptimizations.chunking_strategy);

      // Send first chunk (in real implementation, would handle all chunks)
      if (!outbound.sendText) throw new Error("sendText not available");
      const result = await outbound.sendText({
        cfg: params.cfg,
        to: params.to,
        text: chunks[0],
        deps: params.deps,
      });

      return {
        ...result,
        meta: {
          ...result.meta,
          brain_optimized: true,
          chunking_strategy: params.brainOptimizations.chunking_strategy,
          chunks_total: chunks.length,
        },
      };
    },
    sendMedia: outbound.sendMedia
      ? async (caption: string, mediaUrl: string) => {
          return outbound.sendMedia!({
            cfg: params.cfg,
            to: params.to,
            text: caption,
            mediaUrl,
            deps: params.deps,
          });
        }
      : undefined,
  };
}

function chunkByStrategy(text: string, strategy: string): string[] {
  switch (strategy) {
    case "paragraph":
      return text.split("\n\n").filter((chunk) => chunk.trim());
    case "sentence":
      return text.split(/[.!?]+/).filter((chunk) => chunk.trim());
    case "thematic":
      // Simple thematic chunking - in reality would use brain analysis
      return text.split("\n").filter((chunk) => chunk.trim());
    default:
      return [text];
  }
}

// Enhanced version of existing deliver function with brain integration
export async function brainEnhancedDeliver(params: any) {
  // This would wrap the existing deliverOutboundPayloads function
  // with brain-powered optimizations

  console.log("[Brain Outbound] Enhancing delivery with cognitive optimization...");

  // Perform brain analysis on the delivery context
  const contextAnalysis = await brainOptimizer.analyzeCommunicationContext({
    recipient: params.to,
    channel: params.channel,
    content: params.payloads.map((p: any) => p.text).join(" "),
    context: {
      urgency: params.urgency,
      importance: params.importance,
      relationship: params.relationship,
    },
  });

  // Log brain insights
  console.log("[Brain Outbound] Communication insights:", {
    optimal_timing: contextAnalysis.timing_recommendation,
    risk_level: contextAnalysis.risk_assessment,
    confidence: contextAnalysis.confidence,
  });

  // Proceed with enhanced delivery
  return deliverWithBrainOptimization({
    ...params,
    context: contextAnalysis,
  });
}
