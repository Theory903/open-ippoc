import { PainAggregator, PainLevel } from "../physiology/pain-aggregator.js";
import { LifecycleStateMachine } from "./state-machine.js";

export class HealthCoordinator {
  constructor(
    private sm: LifecycleStateMachine,
    private pain: PainAggregator,
  ) {}

  monitor(): void {
    const agg = this.pain.getAggregate();
    if (agg.level === PainLevel.CRITICAL) {
      this.sm.transition("DEGRADED");
    }
  }
}
