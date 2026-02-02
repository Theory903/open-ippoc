import { Type } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk";
import { executeIppocTool, type ToolEnvelope } from "./gateway.js";

const OrganismCapabilitySchema = Type.Object({
  domain: Type.Union([
    Type.Literal("memory"),
    Type.Literal("body"),
    Type.Literal("evolution"),
    Type.Literal("cognition"),
    Type.Literal("economy"),
    Type.Literal("social"),
    Type.Literal("simulation")
  ]),
  action: Type.String({ description: "Specific action e.g. 'digest_paper', 'propose_patch'" }),
  tool_name: Type.Optional(Type.String({ description: "Specific tool name override, defaults to domain" })),
  parameters: Type.Record(Type.String(), Type.Any(), { description: "Context parameters for the tool" }),
  justification: Type.String({ description: "Why do you need this? Used for audit." })
});

export function registerGenericTool(api: OpenClawPluginApi) {
  
  api.registerTool((context) => {
    return {
      name: "use_organism_capability",
      label: "Use IPPOC Organ",
      description: "Invoke advanced cognitive organs (Research, Evolution, Simulation). Use this for complex tasks like reading papers, running simulations, or self-patching.",
      parameters: OrganismCapabilitySchema,
      execute: async (_id, params: any) => {
        const { config } = context;
        const apiKey = config?.ippocApiKey || process.env.IPPOC_API_KEY || "";
        const baseUrl = config?.ippocNodeUrl || process.env.IPPOC_BRAIN_URL || "http://localhost:8001";

        try {
            const envelope: ToolEnvelope = {
                tool_name: params.tool_name || params.domain,
                domain: params.domain,
                action: params.action,
                context: params.parameters || {},
                // Mapping justification to context for audit
                risk_level: "medium", // Default to medium for generic usage
                estimated_cost: 0.0 // Managed by Brain
            };
            
            // Add justification to context
            envelope.context._justification = params.justification;

            const result = await executeIppocTool(envelope, baseUrl, apiKey);
            
            return {
                content: [{ type: "text", text: JSON.stringify(result.output, null, 2) }],
                details: { 
                    provider: "ippoc-spine", 
                    cost: result.cost_spent,
                    success: result.success,
                    warnings: result.warnings
                }
            };
        } catch (err: any) {
             return {
                content: [{ type: "text", text: `Organ Failure: ${err.message}` }]
            };
        }
      }
    } as AnyAgentTool;
  });
}
