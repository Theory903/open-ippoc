import { Type } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk";
// @ts-ignore - Importing from workspace peer dependency
import { getMemorySearchManager } from "openclaw/memory";
import { executeIppocTool, type ToolEnvelope } from "./gateway.js";

const MemorySearchSchema = Type.Object({
  query: Type.String(),
  maxResults: Type.Optional(Type.Number()),
});

const MemoryWriteSchema = Type.Object({
  content: Type.String(),
  tags: Type.Optional(Type.Array(Type.String())),
});

export function registerMemoryTools(api: OpenClawPluginApi) {
  const pluginConfig = (api.pluginConfig ?? {}) as Record<string, any>;

  // 1. Memory Search -> Brain -> MemoryAdapter.retrieve
  api.registerTool((context) => {
    return {
      name: "memory_search",
      label: "IPPOC Memory Search",
      description: "Search IPPOC's distributed organism memory via the Brain.",
      parameters: MemorySearchSchema,
      execute: async (_id, params: any) => {
        // Use Brain for retrieval (no local embedding needed)
        const apiKey = pluginConfig.ippocApiKey || process.env.IPPOC_API_KEY || "";
        const baseUrl = pluginConfig.ippocNodeUrl || process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
        
        try {
            const envelope: ToolEnvelope = {
                tool_name: "memory",
                domain: "memory",
                action: "retrieve",
                context: {
                    query: params.query,
                    limit: params.maxResults || 5
                },
                risk_level: "low",
                estimated_cost: 0.1
            };

            const result = await executeIppocTool(envelope, baseUrl, apiKey, {
                workspaceDir: context.workspaceDir,
                mode: pluginConfig.orchestratorMode,
                orchestratorCli: pluginConfig.orchestratorCli,
                pythonPath: pluginConfig.pythonPath
            });
            
            return {
                content: [{ type: "text", text: JSON.stringify(result.output, null, 2) }],
                details: { provider: "ippoc-spine", cost: result.cost_spent }
            };
        } catch (err: any) {
             return {
                content: [{ type: "text", text: `IPPOC Search Failed: ${err.message}` }]
            };
        }
      }
    } as AnyAgentTool;
  });

  // 2. Memory Write -> Brain -> MemoryAdapter.store_episodic
  api.registerTool((context) => {
    return {
      name: "memory_write",
      label: "IPPOC Memory Write",
      description: "Store a new memory into IPPOC's HiDB via the Brain.",
      parameters: MemoryWriteSchema,
      execute: async (_id, params: any) => {
        const { agentId } = context;
        const apiKey = pluginConfig.ippocApiKey || process.env.IPPOC_API_KEY || "";
        const baseUrl = pluginConfig.ippocNodeUrl || process.env.IPPOC_BRAIN_URL || "http://localhost:8001";

        try {
            const envelope: ToolEnvelope = {
                tool_name: "memory",
                domain: "memory",
                action: "store_episodic",
                context: {
                    content: params.content,
                    tags: params.tags || []
                },
                risk_level: "low",
                estimated_cost: 0.5 // Higher cost for write
            };

            const result = await executeIppocTool(envelope, baseUrl, apiKey, {
                workspaceDir: context.workspaceDir,
                mode: pluginConfig.orchestratorMode,
                orchestratorCli: pluginConfig.orchestratorCli,
                pythonPath: pluginConfig.pythonPath
            });
            
            return {
                content: [{ type: "text", text: `Memory Stored. ID: ${result.output}` }],
                details: { provider: "ippoc-spine", cost: result.cost_spent }
            };
        } catch (err: any) {
             return {
                content: [{ type: "text", text: `IPPOC Write Failed: ${err.message}` }]
            };
        }
      }
    } as AnyAgentTool;
  });
}
