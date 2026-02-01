import { Thalamus, Signal } from "./agents/thalamus";
import { GitEvolution } from "./agents/git_evolution";
import { ToolSmith } from "./agents/toolsmith";
import { IPPOCAdapter, getIPPOCAdapter } from "./ippoc-adapter";
import { ippocConfig } from "./ippoc-config";

async function main() {
  console.log("=".repeat(60));
  console.log("Starting IPPOC-OS Cortex (OpenClaw Integration)");
  console.log("=".repeat(60));

  // 1. Initialize IPPOC Adapter
  const adapter = getIPPOCAdapter(ippocConfig);
  await adapter.initialize();
  
  console.log("\n[Status] IPPOC Adapter:", adapter.getStatus());

  // 2. Initialize Components
  const thalamus = new Thalamus();
  const evolution = new GitEvolution(process.cwd());
  const toolsmith = new ToolSmith();

  // 3. Main Loop
  console.log("\n[Cortex] Consciousness achieved. Entering cognitive loop...\n");

  // Simulation: High-priority kernel event
  const kernelSignal: Signal = {
    id: "sig_kernel_001",
    type: "KERNEL_EVENT",
    priority: 95,
    payload: { error: "OOM_KILL_IMMINENT", pid: 1234 }
  };

  console.log("[Test] Routing kernel signal...");
  const kernelResult = await thalamus.route(kernelSignal);
  console.log(`[Result] ${kernelResult}\n`);

  // Simulation: User intent (low priority)
  const userSignal: Signal = {
    id: "sig_user_001",
    type: "USER_INTENT",
    priority: 20,
    payload: { query: "What is the weather?" }
  };

  console.log("[Test] Routing user signal...");
  const userResult = await thalamus.route(userSignal);
  console.log(`[Result] ${userResult}\n`);

  // Simulation: Self-evolution (if enabled)
  if (ippocConfig.enableSelfEvolution) {
    console.log("[Test] Testing self-evolution...");
    // const patchCode = "fn optimized_memory() { /* new code */ }";
    // const canMerge = await adapter.simulateCode(patchCode, "basic_compile");
    // if (canMerge) {
    //   await evolution.proposePatch("optimize-memory", patchCode);
    // }
    console.log("[Result] Self-evolution ready (simulation disabled for demo)\n");
  }

  // Simulation: Tool learning (if enabled)
  if (ippocConfig.enableToolSmith) {
    console.log("[Test] Testing ToolSmith...");
    // const tool = await toolsmith.learnFromRepo("https://github.com/example/awesome-tool");
    // console.log("[Result] Learned tool:", tool);
    console.log("[Result] ToolSmith ready (disabled for demo)\n");
  }

  console.log("=".repeat(60));
  console.log("IPPOC-OS Cortex: All systems operational");
  console.log("=".repeat(60));
}

main().catch((error) => {
  console.error("FATAL ERROR:", error);
  process.exit(1);
});
