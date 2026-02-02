import { Type, type Static } from "@sinclair/typebox";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { spawn } from "node:child_process";
import { once } from "node:events";
import fs from "node:fs";
import path from "node:path";

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

type OrchestratorMode = "local" | "http" | "auto";
type ExecuteOptions = {
  mode?: OrchestratorMode;
  workspaceDir?: string;
  pythonPath?: string;
  orchestratorCli?: string;
};

async function readStream(stream: NodeJS.ReadableStream): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf-8");
}

function resolveRepoRoot(workspaceDir?: string): string {
  const start = workspaceDir || process.env.IPPOC_REPO_ROOT || process.cwd();
  let current = path.resolve(start);
  for (let i = 0; i < 6; i += 1) {
    if (fs.existsSync(path.join(current, "brain", "core", "orchestrator.py"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return start;
}

async function executeIppocToolLocal(
  envelope: ToolEnvelope,
  opts: ExecuteOptions,
): Promise<ToolResult> {
  const repoRoot = resolveRepoRoot(opts.workspaceDir);
  const pythonPath = opts.pythonPath || process.env.IPPOC_PYTHON || "python3";
  const cliPath =
    opts.orchestratorCli ||
    process.env.IPPOC_ORCH_CLI ||
    path.join(repoRoot, "brain", "core", "orchestrator_cli.py");

  if (!fs.existsSync(cliPath)) {
    throw new Error(`IPPOC orchestrator CLI not found: ${cliPath}`);
  }

  const proc = spawn(pythonPath, [cliPath], {
    stdio: ["pipe", "pipe", "pipe"],
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });

  proc.stdin.write(JSON.stringify(envelope));
  proc.stdin.end();

  const [stdout, stderr, exitInfo] = await Promise.all([
    readStream(proc.stdout),
    readStream(proc.stderr),
    once(proc, "close"),
  ]);

  const code = Array.isArray(exitInfo) ? exitInfo[0] : exitInfo;
  if (code !== 0 && stdout.trim().length === 0) {
    throw new Error(`IPPOC orchestrator failed (code ${code}): ${stderr.trim()}`);
  }

  try {
    return JSON.parse(stdout) as ToolResult;
  } catch (err: any) {
    throw new Error(`IPPOC orchestrator returned invalid JSON: ${err.message}\n${stderr}`);
  }
}

export async function executeIppocTool(
  envelope: ToolEnvelope,
  baseUrl: string = process.env.IPPOC_BRAIN_URL || "http://localhost:8001",
  apiKey: string = "",
  options: ExecuteOptions = {}
): Promise<ToolResult> {
  const mode = (options.mode || process.env.IPPOC_ORCHESTRATOR_MODE || "auto").toLowerCase() as OrchestratorMode;

  if (mode !== "http") {
    try {
      return await executeIppocToolLocal(envelope, options);
    } catch (err: any) {
      if (mode === "local") {
        throw new Error(`Failed to execute IPPOC tool '${envelope.tool_name}': ${err.message}`);
      }
    }
  }

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
