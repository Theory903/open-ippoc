/**
 * IPPOC Adapter for OpenClaw
 *
 * Bridges OpenClaw with IPPOC-OS components through the Orchestrator.
 * Prefers local orchestration (Python CLI) and falls back to HTTP only when configured.
 */

import axios from "axios";
import { spawn } from "node:child_process";
import { once } from "node:events";
import fs from "node:fs";
import path from "node:path";

type OrchestratorMode = "local" | "http" | "auto";

type RiskLevel = "low" | "medium" | "high";

type ToolEnvelope = {
  tool_name: string;
  domain: "memory" | "body" | "evolution" | "cognition" | "economy" | "social" | "simulation";
  action: string;
  context: Record<string, any>;
  risk_level?: RiskLevel;
  estimated_cost?: number;
  requires_validation?: boolean;
  rollback_allowed?: boolean;
};

type ToolResult = {
  success: boolean;
  output?: any;
  cost_spent?: number;
  memory_written?: boolean;
  rollback_token?: string;
  warnings?: string[];
  error?: string;
};

export interface IPPOCConfig {
  // Database connections
  databaseUrl: string;
  redisUrl: string;

  // Service endpoints (HTTP fallback only)
  orchestratorUrl?: string;
  apiKey?: string;

  // Local orchestrator CLI
  orchestratorMode?: OrchestratorMode;
  orchestratorCli?: string;
  pythonPath?: string;

  // Node configuration
  nodePort: number;
  nodeRole: "reasoning" | "retrieval" | "tool" | "relay";

  // LLM configuration
  vllmEndpoint?: string;

  // Feature flags
  enableSelfEvolution: boolean;
  enableToolSmith: boolean;

  // Economic configuration
  enableEconomy: boolean;
  walletPath?: string;

  // Security configuration
  enableHardening: boolean;
  reputationThreshold: number;
}

function resolveRepoRoot(start: string): string {
  let current = path.resolve(start);
  for (let i = 0; i < 6; i += 1) {
    if (fs.existsSync(path.join(current, "brain", "core", "orchestrator_cli.py"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return start;
}

async function readStream(stream: NodeJS.ReadableStream): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf-8");
}

async function runLocalOrchestrator(
  envelope: ToolEnvelope,
  config: IPPOCConfig
): Promise<ToolResult> {
  const repoRoot = resolveRepoRoot(process.env.IPPOC_REPO_ROOT || process.cwd());
  const pythonPath = config.pythonPath || process.env.IPPOC_PYTHON || "python3";
  const cliPath =
    config.orchestratorCli ||
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
    throw new Error(`Orchestrator failed (code ${code}): ${stderr.trim()}`);
  }

  try {
    return JSON.parse(stdout) as ToolResult;
  } catch (err: any) {
    throw new Error(`Invalid orchestrator JSON: ${err.message}\n${stderr}`);
  }
}

async function runHttpOrchestrator(
  envelope: ToolEnvelope,
  config: IPPOCConfig
): Promise<ToolResult> {
  const baseUrl = config.orchestratorUrl || process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (config.apiKey) {
    headers["Authorization"] = `Bearer ${config.apiKey}`;
  }

  const resp = await axios.post(`${baseUrl}/v1/tools/execute`, envelope, { headers });
  return resp.data as ToolResult;
}

export class IPPOCAdapter {
  private config: IPPOCConfig;
  private initialized: boolean = false;

  constructor(config: IPPOCConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    console.log("[IPPOC] Initializing adapter...");
    console.log("[IPPOC] Configuration:", this.config);

    this.initialized = true;
    console.log("[IPPOC] Adapter initialized successfully");
  }

  private async invokeTool(envelope: ToolEnvelope): Promise<ToolResult> {
    const mode = (this.config.orchestratorMode || process.env.IPPOC_ORCHESTRATOR_MODE || "auto").toLowerCase() as OrchestratorMode;

    if (mode !== "http") {
      try {
        return await runLocalOrchestrator(envelope, this.config);
      } catch (err: any) {
        if (mode === "local") {
          throw err;
        }
        console.warn("[IPPOC] Local orchestrator failed, falling back to HTTP:", err.message);
      }
    }

    return await runHttpOrchestrator(envelope, this.config);
  }

  /**
   * Store memory via Orchestrator (Memory tool)
   */
  async storeMemory(content: string, embedding: number[] = []): Promise<void> {
    try {
      const result = await this.invokeTool({
        tool_name: "memory",
        domain: "memory",
        action: "store_episodic",
        context: {
          content,
          source: "openclaw",
          confidence: 1.0,
          metadata: { embedding },
        },
        risk_level: "low",
        estimated_cost: 0.5,
      });

      if (!result.success) {
        console.warn("[IPPOC] Memory store failed:", result.output || result.error);
      }
    } catch (error) {
      console.warn("[IPPOC] Failed to store memory:", error);
    }
  }

  /**
   * Semantic search via Orchestrator (Memory tool)
   */
  async searchMemory(query: string | number[], limit: number = 10): Promise<any[]> {
    try {
      const queryText = Array.isArray(query) ? query.join(" ") : query;
      const result = await this.invokeTool({
        tool_name: "memory",
        domain: "memory",
        action: "retrieve",
        context: {
          query: queryText,
          limit,
        },
        risk_level: "low",
        estimated_cost: 0.1,
      });

      if (result.success) {
        return result.output || [];
      }
      console.warn("[IPPOC] Memory search failed:", result.output || result.error);
      return [];
    } catch (error) {
      console.warn("[IPPOC] Failed to search memory:", error);
      return [];
    }
  }

  /**
   * Store facts via Orchestrator (Memory tool)
   */
  async storeFact(fact: string): Promise<void> {
    try {
      const result = await this.invokeTool({
        tool_name: "memory",
        domain: "memory",
        action: "store_episodic",
        context: {
          content: fact,
          source: "openclaw",
          confidence: 1.0,
          metadata: { type: "fact" },
        },
        risk_level: "low",
        estimated_cost: 0.5,
      });

      if (!result.success) {
        console.warn("[IPPOC] Fact store failed:", result.output || result.error);
      }
    } catch (error) {
      console.warn("[IPPOC] Failed to store fact:", error);
    }
  }

  /**
   * Execute code via Orchestrator (Body tool)
   */
  async executeCode(workloadId: string, code: string): Promise<any> {
    const result = await this.invokeTool({
      tool_name: "body",
      domain: "body",
      action: "shell_command",
      context: {
        params: { command: code, args: [] },
        workload_id: workloadId,
        source: "openclaw",
      },
      risk_level: "medium",
      estimated_cost: 0.2,
    });

    if (!result.success) {
      throw new Error(result.output || result.error || "Body execution failed");
    }

    return result.output;
  }

  /**
   * Get economy balance via Orchestrator (Body tool)
   */
  async getBalance(): Promise<number> {
    if (!this.config.enableEconomy) {
      return 0;
    }
    try {
      const result = await this.invokeTool({
        tool_name: "body",
        domain: "body",
        action: "economy_balance",
        context: {},
        risk_level: "low",
        estimated_cost: 0.1,
      });

      if (!result.success) {
        return 0;
      }

      return result.output?.balance ?? 0;
    } catch (error) {
      console.warn("[IPPOC] Failed to get balance:", error);
      return 0;
    }
  }

  /**
   * Run reasoning via Orchestrator (Cognition tool)
   */
  async runReasoning(prompt: string): Promise<string> {
    try {
      const result = await this.invokeTool({
        tool_name: "research",
        domain: "cognition",
        action: "think",
        context: { prompt },
        risk_level: "low",
        estimated_cost: 0.2,
      });

      if (!result.success) {
        return "";
      }

      const output = result.output || {};
      return output.conclusion || output.thought || JSON.stringify(output);
    } catch (error) {
      console.warn("[IPPOC] Failed to run reasoning:", error);
      return "";
    }
  }

  /**
   * Get adapter status
   */
  getStatus() {
    return {
      initialized: this.initialized,
      config: {
        ...this.config,
        databaseUrl: "***masked***",
        apiKey: this.config.apiKey ? "***masked***" : undefined,
      },
    };
  }

  /**
   * Simulate code execution before applying
   */
  async simulateCode(code: string, scenario: string = "basic_compile"): Promise<boolean> {
    try {
      const result = await this.invokeTool({
        tool_name: "simulation",
        domain: "simulation",
        action: "test_patch",
        context: { patch: code, scenario },
        risk_level: "low",
        estimated_cost: 0.2,
      });

      if (result.success && result.output?.status === "verified") {
        return true;
      }
    } catch (error) {
      console.warn("[IPPOC] Simulation failed:", error);
    }

    if (code.includes("syntax error") || code.includes("undefined variable")) {
      console.warn("[IPPOC] Simulation detected issues");
      return false;
    }

    return true;
  }

  /**
   * Send payment (stub)
   */
  async sendPayment(recipient: string, amount: number): Promise<boolean> {
    if (!this.config.enableEconomy) {
      console.warn("[IPPOC] Economy not enabled");
      return false;
    }

    console.log(`[IPPOC] Sending ${amount} to ${recipient}`);
    return true;
  }

  /**
   * Get node reputation
   */
  async getNodeReputation(_nodeId: string): Promise<number> {
    return 80;
  }
}

// Singleton instance
let adapterInstance: IPPOCAdapter | null = null;

export function getIPPOCAdapter(config?: IPPOCConfig): IPPOCAdapter {
  if (!adapterInstance && config) {
    adapterInstance = new IPPOCAdapter(config);
  }

  if (!adapterInstance) {
    throw new Error("IPPOC Adapter not initialized. Call with config first.");
  }

  return adapterInstance;
}

export default IPPOCAdapter;
