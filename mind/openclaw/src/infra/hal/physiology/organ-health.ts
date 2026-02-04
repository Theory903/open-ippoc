export type HealthStatus = "ALIVE" | "DEAD" | "DEGRADED";

export enum OrganStatus {
  ALIVE = "ALIVE",
  DEAD = "DEAD",
  DEGRADED = "DEGRADED",
  HEALTHY = "ALIVE", // Alias for compatibility
}

export interface HealthReport {
  status: HealthStatus;
  reason?: string;
  metrics?: Record<string, number>;
}

export class OrganHealth {
  check(target: any): HealthReport {
    // Check process health via system existence check
    // Returns basic health report based on PID vitality

    if (target && target.process) {
      if (target.process.killed || target.process.exitCode !== null) {
        return { status: "DEAD", reason: "Process exited" };
      }
      // Future: Check excessive memory or CPU usage for DEGRADED state
    }

    return { status: "ALIVE" };
  }
}
