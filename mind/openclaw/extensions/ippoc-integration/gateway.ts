import { Type, type Static } from "@sinclair/typebox";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

// --- Schema Definitions matches Python ToolInvocationEnvelope ---

export const ToolEnvelopeSchema = Type.Object({
  tool_name: Type.String(),
  domain: Type.Union([
    Type.Literal("memory"),
    Type.Literal("body"),
    Type.Literal("evolution"),
    Type.Literal("cognition"),
    Type.Literal("economy"),
    Type.Literal("social"),
    Type.Literal("simulation")
  ]),
  action: Type.String(),
  context: Type.Record(Type.String(), Type.Any()),
  risk_level: Type.Optional(Type.Union([
    Type.Literal("low"),
    Type.Literal("medium"),
    Type.Literal("high")
  ])),
  estimated_cost: Type.Optional(Type.Number()),
});

export type ToolEnvelope = Static<typeof ToolEnvelopeSchema>;

export const ToolResultSchema = Type.Object({
  success: Type.Boolean(),
  output: Type.Any(),
  cost_spent: Type.Number(),
  memory_written: Type.Boolean(),
  warnings: Type.Array(Type.String()),
});

export type ToolResult = Static<typeof ToolResultSchema>;

// --- Gateway Client ---

export async function executeIppocTool(
  envelope: ToolEnvelope,
  baseUrl: string = process.env.IPPOC_BRAIN_URL || "http://localhost:8001",
  apiKey: string = ""
): Promise<ToolResult> {
  const url = `${baseUrl}/v1/tools/execute`;
  
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) {
    headers["Authorization"] = `Bearer ${apiKey}`;
  }
  
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(envelope),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      // Handle known error formats from FastAPI
      let detail = errText;
      try {
          const jsonErr = JSON.parse(errText);
          if (jsonErr.detail) detail = jsonErr.detail;
      } catch {}
      
      throw new Error(`IPPOC Gateway Error (${resp.status}): ${detail}`);
    }

    const result = await resp.json();
    return result as ToolResult;
    
  } catch (err: any) {
    throw new Error(`Failed to execute IPPOC tool '${envelope.tool_name}': ${err.message}`);
  }
}
