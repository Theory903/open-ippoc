/**
 * IPPOC Adapter for OpenClaw
 *
 * Bridges OpenClaw with IPPOC-OS components through the Orchestrator.
 * Prefers local orchestration (Python CLI) and falls back to HTTP only when configured.
 */
type OrchestratorMode = "local" | "http" | "auto";
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
    enableEconomy: boolean;
    walletPath?: string;
    enableHardening: boolean;
    reputationThreshold: number;
}
export declare class IPPOCAdapter {
    private config;
    private initialized;
    constructor(config: IPPOCConfig);
    initialize(): Promise<void>;
    private invokeTool;
    /**
     * Store memory via Orchestrator (Memory tool)
     */
    storeMemory(content: string, embedding?: number[]): Promise<void>;
    /**
     * Semantic search via Orchestrator (Memory tool)
     */
    searchMemory(query: string | number[], limit?: number): Promise<any[]>;
    /**
     * Store facts via Orchestrator (Memory tool)
     */
    storeFact(fact: string): Promise<void>;
    /**
     * Execute code via Orchestrator (Body tool)
     */
    executeCode(workloadId: string, code: string): Promise<any>;
    /**
     * Get economy balance via Orchestrator (Body tool)
     */
    getBalance(): Promise<number>;
    /**
     * Run reasoning via Orchestrator (Cognition tool)
     */
    runReasoning(prompt: string): Promise<string>;
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
            enableEconomy: boolean;
            walletPath?: string | undefined;
            enableHardening: boolean;
            reputationThreshold: number;
            databaseUrl: string;
            apiKey: string | undefined;
        };
    };
    /**
     * Simulate code execution before applying
     */
    simulateCode(code: string, scenario?: string): Promise<boolean>;
    /**
     * Send payment (stub)
     */
    sendPayment(recipient: string, amount: number): Promise<boolean>;
    /**
     * Get node reputation
     */
    getNodeReputation(_nodeId: string): Promise<number>;
}
export declare function getIPPOCAdapter(config?: IPPOCConfig): IPPOCAdapter;
export default IPPOCAdapter;
