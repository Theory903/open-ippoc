import { spawn, ChildProcess } from "child_process";
import { OrganHealth } from "./organ-health.js";

export interface SidecarConfig {
  modelPath: string;
  env: Record<string, string>;
}

export interface Sidecar {
  name: string;
  process: ChildProcess;
  startedAt: number;
  restarts: number;
  config: SidecarConfig;
}

export class SidecarOrchestrator {
  private sidecars = new Map<string, Sidecar>();
  private healthMonitor: OrganHealth;
  private checkInterval: NodeJS.Timeout | null = null; // Store interval to clear it

  constructor() {
    this.healthMonitor = new OrganHealth();
  }

  async startSidecar(name: string, modelPath: string, config: SidecarConfig): Promise<void> {
    const child = spawn(
      config.modelPath.endsWith(".js") || config.modelPath.endsWith(".ts")
        ? "node"
        : config.modelPath,
      [
        // pass args if needed, for now assume executable or script
        ...(config.modelPath.endsWith(".js") || config.modelPath.endsWith(".ts")
          ? [config.modelPath]
          : []),
      ],
      {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env, ...config.env },
      },
    );

    const sidecar: Sidecar = {
      name,
      process: child,
      startedAt: Date.now(),
      restarts: 0,
      config,
    };

    this.sidecars.set(name, sidecar);
    this.monitorHealth(sidecar);
  }

  // Allow in-process or external sidecars to register themselves
  registerSidecar(params: {
    name: string;
    pid: number;
    healthCheck: () => Promise<any>;
    restart: () => Promise<void>;
  }): void {
    console.log(`[Sidecar] Registered external sidecar: ${params.name}`);
    // Store as a pseudo-sidecar (some fields like process are unavailable/mocked for external/in-proc)
    // For type compatibility we cast, or we should enhance the Sidecar interface to allow 'external' types.
    // Here we assume it's managed externally but tracked for health.
    // We essentially just track it for health monitoring if we had a way to probe it.
    // Since healthCheck is passed, we can wrap it.

    const sidecar: Sidecar = {
      name: params.name,
      process: { pid: params.pid } as any, // minimal interface
      startedAt: Date.now(),
      restarts: 0,
      config: { modelPath: "external", env: {} },
    };
    this.sidecars.set(params.name, sidecar);

    // Monitor using the provided check
    setInterval(async () => {
      try {
        const h = await params.healthCheck();
        if (h.status !== "ALIVE") console.warn(`external sidecar ${params.name} unstable`);
      } catch (e) {
        console.error(`external sidecar ${params.name} check failed`, e);
      }
    }, 5000);
  }

  public monitorHealth(sidecar: Sidecar): void {
    // Clear previous interval if this sidecar was restarted to avoid duplicate monitors
    // Enforces one active health check loop per sidecar instance

    const healthCheck = setInterval(() => {
      const health = this.healthMonitor.check(sidecar);

      if (health.status === "DEAD") {
        console.error(`Sidecar ${sidecar.name} died. Restarting...`);
        clearInterval(healthCheck); // Stop monitoring dead process
        this.restart(sidecar).catch(console.error);
      } else if (health.status === "DEGRADED") {
        console.warn(`Sidecar ${sidecar.name} is degraded: ${health.reason}`);
      }
    }, 5000);

    // Also clear interval on process exit to be safe
    sidecar.process.on("exit", () => {
      clearInterval(healthCheck);
    });
  }

  private async restart(sidecar: Sidecar): Promise<void> {
    sidecar.restarts++;

    if (sidecar.restarts > 3) {
      throw new Error(`Sidecar ${sidecar.name} failed ${sidecar.restarts} times. Giving up.`);
    }

    // Ensure it's dead
    sidecar.process.kill();

    // Restart logic would realistically wait a bit
    // Here we recursively call startSidecar logic or reuse logic.
    // For simplicity, we just "re-start" by calling startSidecar again with same config.
    this.sidecars.delete(sidecar.name); // Remove old reference
    await this.startSidecar(sidecar.name, sidecar.config.modelPath, sidecar.config);
  }

  // Method to manually stop for testing/shutdown
  stopAll() {
    for (const sidecar of Array.from(this.sidecars.values())) {
      sidecar.process.kill();
    }
    this.sidecars.clear();
  }
}
