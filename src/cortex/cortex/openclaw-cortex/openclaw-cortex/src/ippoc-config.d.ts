/**
 * IPPOC-OS Configuration for OpenClaw
 *
 * This configuration overrides OpenClaw's defaults to use IPPOC components
 */
import { type IPPOCConfig } from './ippoc-adapter.js';
export declare const ippocConfig: IPPOCConfig;
/**
 * OpenClaw-compatible configuration
 * Maps IPPOC concepts to OpenClaw's expected structure
 */
export declare const openclawConfig: {
    memory: {
        provider: string;
        config: {
            databaseUrl: string;
            redisUrl: string;
        };
    };
    llm: {
        provider: string;
        endpoint: string | undefined;
        model: string;
    };
    features: {
        gateway: boolean;
        channels: boolean;
    };
};
