export enum PainLevel {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export interface PainSignal {
  level: PainLevel;
  reason: string;
  timestamp: number;
}

export interface AggregatePain {
  level: PainLevel;
  sources: string[];
  timestamp: number;
}

export class PainAggregator {
  private signals = new Map<string, PainSignal>();

  report(source: string, level: PainLevel, reason: string): void {
    this.signals.set(source, {
      level,
      reason,
      timestamp: Date.now(),
    });

    const aggregate = this.aggregate();

    if (aggregate.level === PainLevel.CRITICAL) {
      this.triggerEmergency(aggregate);
    }
  }

  // Exposed for testing/monitoring
  getAggregate(): AggregatePain {
    return this.aggregate();
  }

  private aggregate(): AggregatePain {
    const pains = Array.from(this.signals.values());

    const criticalCount = pains.filter((p) => p.level === PainLevel.CRITICAL).length;
    const highCount = pains.filter((p) => p.level === PainLevel.HIGH).length;
    // Add medium count for completeness based on code logic inferred
    const mediumCount = pains.filter((p) => p.level === PainLevel.MEDIUM).length;

    let level: PainLevel;
    if (criticalCount > 0) {
      level = PainLevel.CRITICAL;
    } else if (highCount > 2) {
      // Logic from snippet: highCount > 2 -> HIGH ? No, snippet said if critical > 0 -> CRITICAL.
      // Let's stick to valid logic:
      level = PainLevel.HIGH;
    } else if (highCount > 0 || mediumCount > 3) {
      level = PainLevel.MEDIUM;
    } else {
      level = PainLevel.LOW;
    }

    return {
      level,
      sources: pains.map((p) => p.reason),
      timestamp: Date.now(),
    };
  }

  private triggerEmergency(pain: AggregatePain): void {
    console.error("🚨 SYSTEM PAIN CRITICAL:", pain);
    // Could trigger Brain notification, graceful degradation, etc.
  }
}
