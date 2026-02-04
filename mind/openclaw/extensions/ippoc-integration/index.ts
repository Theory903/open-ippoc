import type { OpenClawPluginApi } from "../../src/plugin-sdk/index.js";
import { registerMemoryTools } from "./memory.js";
import { registerGenericTool } from "./generic.js";

const ippocPlugin = {
  id: "ippoc-integration",
  name: "IPPOC Organism Layer",
  description: "Adds memory, learning, economy, and swarm intelligence via IPPOC",
  kind: "organism",
  
  register(api: OpenClawPluginApi) {
    const isEnabled = process.env.IPPOC_ENABLED === "true";
    
    if (!isEnabled) {
      // api.logger might not be available at top level if not passed, but usually is in context
      console.log("[IPPOC] 🔴 Disabled (env.IPPOC_ENABLED != true)");
      return;
    }

    console.log("[IPPOC] 🟢 Organism Layer Active");

    // 1. Register Execution Command (The "Muscle" of the Cron)
    api.registerCommand({
        name: "ippoc_cron",
        description: "Internal command to trigger IPPOC cognitive capabilities",
        acceptsArgs: true,
        handler: async (ctx) => {
            const cronId = ctx.args?.trim();
            if (!cronId) return { text: "Error: No Cron ID provided", isError: true };
            
            console.log(`[IPPOC] 🕒 Triggering Cognitive Loop via Command: ${cronId}`);
            try {
                const resp = await fetch(`${process.env.IPPOC_NODE_URL || "http://localhost:9000"}/v1/ippoc/cron/${cronId}/run`, {
                    method: "POST"
                });
                const result = await resp.json();
                console.log(`[IPPOC] ✅ ${cronId} Complete:`, result);
                return { text: `Executed ${cronId}: ${result.status}` };
            } catch (e: any) {
                console.error(`[IPPOC] ❌ ${cronId} Failed:`, e);
                return { text: `IPPOC Cron Failed: ${e.message}`, isError: true };
            }
        }
    });

    // 2. Sync Logic: Ensure OpenClaw knows about IPPOC's cognitive rhythms
    syncIppocCron(api).catch(err => console.error("[IPPOC] Cron Sync Failed:", err));

    // 3. Register Memory Tools
    registerMemoryTools(api);

    // 4. Register Generic Organism Tool (The Superpower)
    registerGenericTool(api);

    // 5. Register Hooks
    api.registerHook("before_agent_start", async (event, ctx) => {
        // Prompt Injection Point
        api.logger.debug("[IPPOC] 🧠 Injecting context...");
        return {
            prependContext: "\n[IPPOC_CONTEXT]\nThinking...\n[/IPPOC_CONTEXT]\n"
        };
    });

    api.registerHook("agent_end", async (event, ctx) => {
        // Post-Run Analysis
        api.logger.debug("[IPPOC] 📝 Analyzing run...");
    });
  }
};

export default ippocPlugin;

async function syncIppocCron(api: OpenClawPluginApi) {
    const IPPOC_Url = process.env.IPPOC_NODE_URL || "http://localhost:9000";
    
    try {
        // 1. Get IPPOC Capabilities
        const resp = await fetch(`${IPPOC_Url}/v1/ippoc/cron`);
        if (!resp.ok) return; // IPPOC might be offline
        const capabilities = await resp.json();

        // 2. List Existing Jobs
        const existing = await api.cron.list({ includeDisabled: true });
        const existingIds = new Set(existing.jobs.map((j:any) => j.id));

        // 3. Register Missing
        for (const cap of capabilities) {
            if (!existingIds.has(cap.id)) {
                console.log(`[IPPOC] Registering new cognitive organ: ${cap.name}`);
                await api.cron.add({
                    name: cap.name,
                    description: `${cap.description} (Cost: ${cap.cost_estimate.ippc_per_run} IPPC)`,
                    schedule: { kind: "cron", expr: cap.schedule }, 
                    // Use agentTurn to trigger the command
                    payload: { 
                        kind: "agentTurn", 
                        message: `/ippoc_cron ${cap.id}`,
                        // Don't deliver to user, just run internally if possible, 
                        // but agentTurn usually implies user visibility. 
                        // We rely on the command handler intercepting it.
                        model: "fast" // Use cheapest model for the turn envelope
                    },
                    sessionTarget: "main", 
                    wakeMode: "now"
                });
            }
        }
    } catch (err) {
        console.warn("[IPPOC] Could not sync cron (Node offline?):", err);
    }
}
