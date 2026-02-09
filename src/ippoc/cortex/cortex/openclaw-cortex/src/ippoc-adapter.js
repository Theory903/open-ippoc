"use strict";
/**
 * IPPOC Adapter for OpenClaw
 *
 * Bridges OpenClaw with IPPOC-OS components through the Orchestrator.
 * Prefers local orchestration (Python CLI) and falls back to HTTP only when configured.
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.IPPOCAdapter = void 0;
exports.getIPPOCAdapter = getIPPOCAdapter;
const axios_1 = __importDefault(require("axios"));
const node_child_process_1 = require("node:child_process");
const node_events_1 = require("node:events");
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
function resolveRepoRoot(start) {
    let current = node_path_1.default.resolve(start);
    for (let i = 0; i < 6; i += 1) {
        if (node_fs_1.default.existsSync(node_path_1.default.join(current, "brain", "core", "orchestrator_cli.py"))) {
            return current;
        }
        const parent = node_path_1.default.dirname(current);
        if (parent === current)
            break;
        current = parent;
    }
    return start;
}
async function readStream(stream) {
    const chunks = [];
    for await (const chunk of stream) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    }
    return Buffer.concat(chunks).toString("utf-8");
}
async function runLocalOrchestrator(envelope, config) {
    const repoRoot = resolveRepoRoot(process.env.IPPOC_REPO_ROOT || process.cwd());
    const pythonPath = config.pythonPath || process.env.IPPOC_PYTHON || "python3";
    const cliPath = config.orchestratorCli ||
        process.env.IPPOC_ORCH_CLI ||
        node_path_1.default.join(repoRoot, "src", "cortex", "core", "orchestrator_cli.py");
    if (!node_fs_1.default.existsSync(cliPath)) {
        throw new Error(`IPPOC orchestrator CLI not found: ${cliPath}`);
    }
    const proc = (0, node_child_process_1.spawn)(pythonPath, [cliPath], {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });
    proc.stdin.write(JSON.stringify(envelope));
    proc.stdin.end();
    const [stdout, stderr, exitInfo] = await Promise.all([
        readStream(proc.stdout),
        readStream(proc.stderr),
        (0, node_events_1.once)(proc, "close"),
    ]);
    const code = Array.isArray(exitInfo) ? exitInfo[0] : exitInfo;
    if (code !== 0 && stdout.trim().length === 0) {
        throw new Error(`Orchestrator failed (code ${code}): ${stderr.trim()}`);
    }
    try {
        const result = JSON.parse(stdout);
        // Machine-readable JSON with protocol marker
        process.stdout.write("__RESULT__:" + JSON.stringify(result) + "\n");
        return result;
    }
    catch (err) {
        // Try to extract JSON from stdout if it contains non-JSON lines (e.g., log messages)
        const jsonMatch = stdout.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            try {
                const result = JSON.parse(jsonMatch[0]);
                process.stdout.write("__RESULT__:" + JSON.stringify(result) + "\n");
                return result;
            }
            catch {
                // Ignore extraction error, fall through to original error
            }
        }
        throw new Error(`Invalid orchestrator JSON: ${err.message}\n${stderr}`);
    }
}
async function runHttpOrchestrator(envelope, config) {
    const baseUrl = config.orchestratorUrl || process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
    const headers = { "Content-Type": "application/json" };
    if (config.apiKey) {
        headers["Authorization"] = `Bearer ${config.apiKey}`;
    }
    const resp = await axios_1.default.post(`${baseUrl}/v1/tools/execute`, envelope, { headers });
    return resp.data;
}
class IPPOCAdapter {
    config;
    initialized = false;
    constructor(config) {
        this.config = config;
    }
    async initialize() {
        process.stderr.write("[IPPOC] Initializing adapter...\n");
        process.stderr.write(`[IPPOC] Configuration: ${JSON.stringify(this.config)}\n`);
        this.initialized = true;
        process.stderr.write("[IPPOC] Adapter initialized successfully\n");
    }
    async invokeTool(envelope) {
        const mode = (this.config.orchestratorMode || process.env.IPPOC_ORCHESTRATOR_MODE || "auto").toLowerCase();
        if (mode !== "http") {
            try {
                return await runLocalOrchestrator(envelope, this.config);
            }
            catch (err) {
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
    async storeMemory(content, embedding = []) {
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
        }
        catch (error) {
            console.warn("[IPPOC] Failed to store memory:", error);
        }
    }
    /**
     * Semantic search via Orchestrator (Memory tool)
     */
    async searchMemory(query, limit = 10) {
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
        }
        catch (error) {
            console.warn("[IPPOC] Failed to search memory:", error);
            return [];
        }
    }
    /**
     * Store facts via Orchestrator (Memory tool)
     */
    async storeFact(fact) {
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
        }
        catch (error) {
            console.warn("[IPPOC] Failed to store fact:", error);
        }
    }
    /**
     * Execute code via Orchestrator (Body tool)
     */
    async executeCode(workloadId, code) {
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
    async getBalance() {
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
        }
        catch (error) {
            console.warn("[IPPOC] Failed to get balance:", error);
            return 0;
        }
    }
    /**
     * Run reasoning via Orchestrator (Cognition tool)
     */
    async runReasoning(prompt) {
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
        }
        catch (error) {
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
    async simulateCode(code, scenario = "basic_compile") {
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
        }
        catch (error) {
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
    async sendPayment(recipient, amount) {
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
    async getNodeReputation(_nodeId) {
        return 80;
    }
}
exports.IPPOCAdapter = IPPOCAdapter;
// Singleton instance
let adapterInstance = null;
function getIPPOCAdapter(config) {
    if (!adapterInstance && config) {
        adapterInstance = new IPPOCAdapter(config);
    }
    if (!adapterInstance) {
        throw new Error("IPPOC Adapter not initialized. Call with config first.");
    }
    return adapterInstance;
}
exports.default = IPPOCAdapter;
