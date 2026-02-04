export type SystemState = "BOOT" | "HEALTHY" | "DEGRADED" | "MAINTENANCE" | "SHUTDOWN";

export class LifecycleStateMachine {
  private currentState: SystemState = "BOOT";

  transition(to: SystemState): void {
    console.log(`[Lifecycle] Transition: ${this.currentState} -> ${to}`);
    this.currentState = to;
  }

  getState(): SystemState {
    return this.currentState;
  }
}
