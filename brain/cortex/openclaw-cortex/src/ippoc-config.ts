/**
 * IPPOC-OS Configuration for OpenClaw
 * 
 * This configuration overrides OpenClaw's defaults to use IPPOC components
 */

import type { IPPOCConfig } from "./ippoc-adapter";

export const ippocConfig: IPPOCConfig = {
  // Database connections
  databaseUrl: process.env.DATABASE_URL || "postgresql://postgres:ippoc_secret@localhost:5432/ippoc_hidb",
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
  
  // Node configuration
  nodePort: parseInt(process.env.NODE_PORT || "9000"),
  nodeRole: (process.env.NODE_ROLE as any) || "reasoning",
  
  // LLM configuration
  vllmEndpoint: process.env.VLLM_ENDPOINT || "http://localhost:8000/v1",
  
  // Feature flags
  enableSelfEvolution: process.env.ENABLE_SELF_EVOLUTION !== "false",
  enableToolSmith: process.env.ENABLE_TOOLSMITH !== "false",
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
    gateway: false,  // We use nervous-system instead
    channels: false, // Not needed for IPPOC-OS
  },
};
