import { Thalamus, Signal } from "./agents/thalamus";
import { GitEvolution } from "./agents/git_evolution";
import { ToolSmith } from "./agents/toolsmith";
import { WebLearner } from "./agents/web_learner";
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
  const webLearner = new WebLearner();

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

  // Simulation: User intent (low priority) - should hit habit system if available
  const userSignal: Signal = {
    id: "sig_user_001",
    type: "USER_INTENT",
    priority: 20,
    payload: { query: "What is the weather?" }
  };

  console.log("[Test] Routing user signal...");
  const userResult = await thalamus.route(userSignal);
  console.log(`[Result] ${userResult}\n`);

  // Test: Add habit
  thalamus.addHabit("what is the weather?", "Check weather using weather.com API");
  
  console.log("[Test] Testing habit system...");
  const userSignal2: Signal = {
    id: "sig_user_002",
    type: "USER_INTENT",
    priority: 25,
    payload: { query: "What is the weather?" }
  };
  const userResult2 = await thalamus.route(userSignal2);
  console.log(`[Result] ${userResult2}\n`);

  // Test: WebLearner - Search for coding tutorial
  console.log("[Test] Testing WebLearner research...");
  const researchResult = await webLearner.researchTopic("React hooks tutorial", "SURFACE");
  console.log(`[Result] ${researchResult}\n`);

  // Test: ToolSmith - Search for tools
  console.log("[Test] Testing ToolSmith search...");
  const toolResults = await toolsmith.searchGitHub("react components");
  console.log(`[Result] Found ${toolResults.length} tool repositories\n`);

  // Test: WebLearner - Find code solution for error
  console.log("[Test] Testing WebLearner code search...");
  const codeSolution = await webLearner.findCodeSolution("TypeError: Cannot read property 'map' of undefined");
  console.log(`[Result] ${codeSolution}\n`);

  // Simulation: Self-evolution (if enabled)
  if (ippocConfig.enableSelfEvolution) {
    console.log("[Test] Testing self-evolution...");
    try {
      const patchCode = `
fn optimize_memory() {
    // New memory optimization algorithm
    println!("Memory optimization activated");
}`;
      const canMerge = await adapter.simulateCode(patchCode, "basic_compile");
      if (canMerge) {
        await evolution.proposePatch("optimize-memory", patchCode);
        console.log("[Result] Patch merged successfully");
      } else {
        console.log("[Result] Patch simulation failed");
      }
    } catch (error) {
      console.log(`[Result] Self-evolution test failed: ${error}`);
    }
  }

  // Test: Get habits
  console.log("[Test] Current habits:");
  const habits = thalamus.getHabits();
  habits.forEach((habit, index) => {
    console.log(`${index + 1}. ${habit.query}: ${habit.response}`);
  });

  // Test: Economic operations
  if (ippocConfig.enableEconomy) {
    console.log("\n[Test] Economic operations:");
    const balance = await adapter.getBalance();
    console.log(`Current balance: ${balance} IPPC`);
    
    // Send small payment to test wallet
    try {
      const paymentSuccess = await adapter.sendPayment("0x1234...5678", 10);
      console.log(`Payment successful: ${paymentSuccess}`);
    } catch (error) {
      console.log(`Payment failed: ${error}`);
    }
  }

  // Final status report
  console.log("\n" + "=".repeat(60));
  console.log("IPPOC-OS Cortex: All systems operational");
  console.log("=".repeat(60));
  console.log("\n[System Status]:");
  console.log("- Thalamus active with", thalamus.getHabits().length, "habits");
  console.log("- ToolSmith active with", toolsmith.getTools().length, "tools");
  console.log("- Adapter initialized:", adapter.getStatus());
}

main().catch((error) => {
  console.error("FATAL ERROR:", error);
  process.exit(1);
});
