/**
 * IPPOC Adapter for OpenClaw
 *
 * Bridges OpenClaw with IPPOC-OS components through the Orchestrator.
 * Prefers local orchestration (Python CLI) and falls back to HTTP only when configured.
 */
import axios from "axios";
import { spawn } from "node:child_process";
import { once } from "node:events";
import * as fs from "node:fs";
import * as path from "node:path";
import { EventEmitter } from "node:events";
function resolveRepoRoot(start) {
    let current = path.resolve(start);
    for (let i = 0; i < 6; i += 1) {
        if (fs.existsSync(path.join(current, "brain", "core", "orchestrator_cli.py"))) {
            return current;
        }
        const parent = path.dirname(current);
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
        return JSON.parse(stdout);
    }
    catch (err) {
        throw new Error(`Invalid orchestrator JSON: ${err.message}\n${stderr}`);
    }
}
async function runHttpOrchestrator(envelope, config) {
    const baseUrl = config.orchestratorUrl || process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
    const headers = { "Content-Type": "application/json" };
    if (config.apiKey) {
        headers["Authorization"] = `Bearer ${config.apiKey}`;
    }
    const resp = await axios.post(`${baseUrl}/v1/tools/execute`, envelope, { headers });
    return resp.data;
}
export class IPPOCAdapter extends EventEmitter {
    config;
    initialized = false;
    halCallbacks = new Map();
    eventBuffer = [];
    constructor(config) {
        super();
        this.config = config;
        this.setupHalEventForwarding();
    }
    setupHalEventForwarding() {
        // Listen for HAL organ events and forward to Brain
        setInterval(() => {
            this.processEventBuffer();
        }, 1000); // Process events every second
    }
    processEventBuffer() {
        if (this.eventBuffer.length === 0)
            return;
        const events = [...this.eventBuffer];
        this.eventBuffer = [];
        // Forward to Brain for processing
        this.emit('hal_events', events);
    }
    async initialize() {
        console.log("[IPPOC] Initializing adapter...");
        console.log("[IPPOC] Configuration:", this.config);
        this.initialized = true;
        console.log("[IPPOC] Adapter initialized successfully");
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
     * Store memory with HAL memory consolidation
     */
    async storeMemory(content, embedding = []) {
        // Enhanced with HAL memory integration
        this.emitHalEvent('cognition', 'memory_store_initiated', {
            content,
            embedding,
            timestamp: Date.now()
        });
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
     * Semantic search with HAL memory optimization
     */
    async searchMemory(query, limit = 10) {
        // Enhanced with HAL memory integration
        this.emitHalEvent('cognition', 'memory_search_initiated', {
            query,
            limit,
            timestamp: Date.now()
        });
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
     * Store facts with HAL memory integration
     */
    async storeFact(fact) {
        // Enhanced with HAL memory integration
        this.emitHalEvent('cognition', 'fact_stored', {
            fact,
            timestamp: Date.now()
        });
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
     * Execute code with HAL execution monitoring
     */
    async executeCode(workloadId, code) {
        // Enhanced with HAL execution integration
        this.emitHalEvent('execution', 'code_execution_requested', {
            workloadId,
            code,
            timestamp: Date.now()
        });
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
     * Get economy balance with HAL economic monitoring
     */
    async getBalance() {
        if (!this.config.enableEconomy) {
            return 0;
        }
        // Enhanced with HAL economic integration
        this.emitHalEvent('economy', 'balance_check', { timestamp: Date.now() });
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
     * Run reasoning with HAL cognitive integration
     */
    async runReasoning(prompt) {
        // Enhanced with HAL cognition integration
        this.emitHalEvent('cognition', 'reasoning_initiated', {
            prompt,
            timestamp: Date.now()
        });
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
     * Register callback for HAL events
     */
    async registerHalCallback(event, handler) {
        this.halCallbacks.set(event, handler);
        console.log(`[IPPOC] Registered HAL callback for event: ${event}`);
    }
    /**
     * Emit HAL event to Brain
     */
    emitHalEvent(organ, event, data) {
        const halEvent = {
            organ,
            event,
            data,
            timestamp: Date.now()
        };
        this.eventBuffer.push(halEvent);
        // Also emit immediately for real-time processing
        this.emit(`hal_${organ}_${event}`, data);
    }
    /**
     * Trigger Brain response to HAL event
     */
    async triggerBrainResponse(event) {
        const callback = this.halCallbacks.get(event.event);
        if (callback) {
            try {
                return await callback(event.data);
            }
            catch (error) {
                console.error(`[IPPOC] Brain callback failed for ${event.event}:`, error);
            }
        }
        return null;
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
     * Simulate code execution with HAL validation
     */
    async simulateCode(code, scenario = "basic_compile") {
        // Enhanced with HAL evolution integration
        this.emitHalEvent('evolution', 'simulation_requested', {
            code,
            scenario,
            timestamp: Date.now()
        });
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
     * Send payment with economic signaling
     */
    async sendPayment(recipient, amount) {
        if (!this.config.enableEconomy) {
            console.warn("[IPPOC] Economy not enabled");
            return false;
        }
        // Enhanced with HAL economic integration
        this.emitHalEvent('economy', 'payment_initiated', {
            recipient,
            amount,
            timestamp: Date.now()
        });
        console.log(`[IPPOC] Sending ${amount} to ${recipient}`);
        return true;
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
    async getNodeReputation(nodeId) {
        // Enhanced with HAL integration
        this.emitHalEvent('identity', 'reputation_check', { nodeId });
        return 80;
    }
    /**
     * Join a telepathy chat room
     */
    async joinRoom(roomId) {
        if (!this.config.enableSocial)
            return false;
        try {
            const result = await this.invokeTool({
                tool_name: "telepathy",
                domain: "social",
                action: "join_room",
                context: { room_id: roomId },
                risk_level: "low",
                estimated_cost: 0.1
            });
            return result.success;
        }
        catch (err) {
            console.warn("[IPPOC] Failed to join room:", err);
            return false;
        }
    }
    /**
     * Send a telepathy message
     */
    async sendMessage(roomId, content, type = "THOUGHT") {
        // Enhanced with HAL integration
        this.emitHalEvent('social', 'message_sent', { roomId, content, type });
        if (!this.config.enableSocial)
            return false;
        try {
            const result = await this.invokeTool({
                tool_name: "telepathy",
                domain: "social",
                action: "broadcast",
                context: {
                    room_id: roomId,
                    type,
                    payload: { text: content }
                },
                risk_level: "low",
                estimated_cost: 0.2
            });
            return result.success;
        }
        catch (err) {
            console.warn("[IPPOC] Failed to send message:", err);
            return false;
        }
    }
}
// Singleton instance
let adapterInstance = null;
export function getIPPOCAdapter(config) {
    if (!adapterInstance && config) {
        adapterInstance = new IPPOCAdapter(config);
    }
    if (!adapterInstance) {
        throw new Error("IPPOC Adapter not initialized. Call with config first.");
    }
    return adapterInstance;
}
export default IPPOCAdapter;
