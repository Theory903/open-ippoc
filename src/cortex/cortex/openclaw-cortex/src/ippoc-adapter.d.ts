/**
 * IPPOC Adapter for OpenClaw
 *
 * Bridges OpenClaw with IPPOC-OS components through the Orchestrator.
 * Prefers local orchestration (Python CLI) and falls back to HTTP only when configured.
 */
import { EventEmitter } from "node:events";
type OrchestratorMode = "local" | "http" | "auto";
type HalEvent = {
    organ: "identity" | "execution" | "evolution" | "physiology" | "cognition" | "lifecycle" | "economy" | "social";
    event: string;
    data: any;
    timestamp: number;
};
export interface IPPOCConfig {
    databaseUrl: string;
    redisUrl: string;
    orchestratorUrl?: string;
    apiKey?: string;
    orchestratorMode?: OrchestratorMode;
    orchestratorCli?: string;
    pythonPath?: string;
    nodePort: number;
    nodeRole: "reasoning" | "retrieval" | "tool" | "relay";
    vllmEndpoint?: string;
    enableSelfEvolution: boolean;
    enableToolSmith: boolean;
    enableSocial: boolean;
    enableEconomy: boolean;
    walletPath?: string;
    enableHardening: boolean;
    reputationThreshold: number;
}
export declare class IPPOCAdapter extends EventEmitter {
    private config;
    private initialized;
    private halCallbacks;
    private eventBuffer;
    constructor(config: IPPOCConfig);
    private setupHalEventForwarding;
    private processEventBuffer;
    initialize(): Promise<void>;
    private invokeTool;
    /**
     * Store memory with HAL memory consolidation
     */
    storeMemory(content: string, embedding?: number[]): Promise<void>;
    /**
     * Semantic search with HAL memory optimization
     */
    searchMemory(query: string | number[], limit?: number): Promise<any[]>;
    /**
     * Store facts with HAL memory integration
     */
    storeFact(fact: string): Promise<void>;
    /**
     * Execute code with HAL execution monitoring
     */
    executeCode(workloadId: string, code: string): Promise<any>;
    /**
     * Get economy balance with HAL economic monitoring
     */
    getBalance(): Promise<number>;
    /**
     * Run reasoning with HAL cognitive integration
     */
    runReasoning(prompt: string): Promise<string>;
    /**
     * Register callback for HAL events
     */
    registerHalCallback(event: string, handler: Function): Promise<void>;
    /**
     * Emit HAL event to Brain
     */
    emitHalEvent(organ: HalEvent['organ'], event: string, data: any): void;
    /**
     * Trigger Brain response to HAL event
     */
    triggerBrainResponse(event: HalEvent): Promise<any>;
    /**
     * Get adapter status
     */
    getStatus(): {
        initialized: boolean;
        config: {
            redisUrl: string;
            orchestratorUrl?: string | undefined;
            orchestratorMode?: OrchestratorMode | undefined;
            orchestratorCli?: string | undefined;
            pythonPath?: string | undefined;
            nodePort: number;
            nodeRole: "reasoning" | "relay" | "retrieval" | "tool";
            vllmEndpoint?: string | undefined;
            enableSelfEvolution: boolean;
            enableToolSmith: boolean;
            enableSocial: boolean;
            enableEconomy: boolean;
            walletPath?: string | undefined;
            enableHardening: boolean;
            reputationThreshold: number;
            databaseUrl: string;
            apiKey: string | undefined;
        };
    };
    /**
     * Simulate code execution with HAL validation
     */
    simulateCode(code: string, scenario?: string): Promise<boolean>;
    /**
     * Send payment with economic signaling
     */
    sendPayment(recipient: string, amount: number): Promise<boolean>;
    /**
     * Get node reputation
     */
    getNodeReputation(nodeId: string): Promise<number>;
    /**
     * Join a telepathy chat room
     */
    joinRoom(roomId: string): Promise<boolean>;
    /**
     * Send a telepathy message
     */
    sendMessage(roomId: string, content: string, type?: "THOUGHT" | "QUESTION" | "REVIEW"): Promise<boolean>;
}
export declare function getIPPOCAdapter(config?: IPPOCConfig): IPPOCAdapter;
export default IPPOCAdapter;
