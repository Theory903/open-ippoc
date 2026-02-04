/**
 * IPPOC-OS Configuration for OpenClaw
 *
 * This configuration overrides OpenClaw's defaults to use IPPOC components
 */
import './ippoc-adapter.js';
export const ippocConfig = {
    // Database connections
    databaseUrl: process.env.DATABASE_URL || "postgresql://postgres:ippoc_secret@localhost:5432/ippoc_hidb",
    redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
    // Orchestrator configuration
    orchestratorMode: process.env.IPPOC_ORCHESTRATOR_MODE || "auto",
    orchestratorUrl: process.env.IPPOC_BRAIN_URL || "http://localhost:8001",
    orchestratorCli: process.env.IPPOC_ORCH_CLI,
    pythonPath: process.env.IPPOC_PYTHON,
    apiKey: process.env.IPPOC_API_KEY,
    // Node configuration
    nodePort: parseInt(process.env.NODE_PORT || "9000"),
    nodeRole: process.env.NODE_ROLE || "reasoning",
    // LLM configuration
    vllmEndpoint: process.env.VLLM_ENDPOINT || "http://localhost:8000/v1",
    // Feature flags
    enableSelfEvolution: process.env.ENABLE_SELF_EVOLUTION !== "false",
    enableToolSmith: process.env.ENABLE_TOOLSMITH !== "false",
    enableEconomy: process.env.ENABLE_ECONOMY !== "false",
    enableSocial: process.env.ENABLE_SOCIAL !== "false",
    enableHardening: process.env.ENABLE_HARDENING !== "false",
    // Economic configuration
    walletPath: process.env.WALLET_PATH || "./wallet.json",
    // Security configuration
    reputationThreshold: parseInt(process.env.REPUTATION_THRESHOLD || "80"),
};
/**
 * OpenClaw-compatible configuration
 * Maps IPPOC concepts to OpenClaw's expected structure
 */
export const openclawConfig = {
    // Override memory backend
    memory: {
        provider: "ippoc-hidb",
        config: {
            databaseUrl: ippocConfig.databaseUrl,
            redisUrl: ippocConfig.redisUrl,
        },
    },
    // Override LLM backend
    llm: {
        provider: "vllm",
        endpoint: ippocConfig.vllmEndpoint,
        model: "microsoft/Phi-4-reasoning-plus",
    },
    // Disable OpenClaw's built-in features we replace
    features: {
        gateway: false, // We use nervous-system instead
        channels: false, // Not needed for IPPOC-OS
    },
};
