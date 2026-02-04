export interface DataStream {
  id: string;
  source: string;
  latest(): DataPoint;
}

export interface DataPoint {
  source: string;
  timestamp: number;
  [key: string]: any;
}

export interface FusedState {
  state: Record<string, FusedValue>;
  timestamp: number;
  confidence: number;
  contributingSources: string[];
}

export interface FusedValue {
  value: any;
  confidence: number;
}

export class StreamFusionEngine {
  private streams: Map<string, DataStream> = new Map();
  private sourceTrust: Map<string, number> = new Map();

  constructor() {
    // Init trust
  }

  addStream(stream: DataStream): void {
    this.streams.set(stream.id, stream);
  }

  async getFusedState(): Promise<FusedState> {
    // 1. Get latest from all streams
    const latest = Array.from(this.streams.values()).map((s) => s.latest());

    if (latest.length === 0) {
      return { state: {}, timestamp: Date.now(), confidence: 0, contributingSources: [] };
    }

    // 2. Temporal alignment - allow max 100ms drift
    const aligned = this.temporalAlignment(latest);

    // 3. Semantic fusion
    const semanticallyFused = this.semanticFusion(aligned);

    return {
      state: semanticallyFused,
      timestamp: Date.now(),
      confidence: this.computeFusionConfidence(latest),
      contributingSources: latest.map((d) => d.source),
    };
  }

  private temporalAlignment(data: DataPoint[]): DataPoint[] {
    // Filter out stale data (> 5 seconds old)
    const now = Date.now();
    return data.filter((d) => now - d.timestamp < 5000);
  }

  private semanticFusion(data: DataPoint[]): Record<string, FusedValue> {
    const fused: Record<string, FusedValue> = {};
    const allKeys = new Set<string>();
    data.forEach((d) =>
      Object.keys(d).forEach((k) => {
        if (k !== "source" && k !== "timestamp") allKeys.add(k);
      }),
    );

    for (const field of allKeys) {
      const values = data
        .filter((d) => d[field] !== undefined)
        .map((d) => ({ value: d[field], source: d.source, trust: this.trustScore(d.source) }));

      if (values.length === 0) continue;

      const uniqueValues = new Set(values.map((v) => JSON.stringify(v.value)));

      if (uniqueValues.size === 1) {
        // Consensus
        fused[field] = { value: values[0].value, confidence: 1.0 };
      } else {
        // Weighted vote
        // Calculate weighted average for numeric, or max-trust for categorical
        const isNumeric = typeof values[0].value === "number";

        if (isNumeric) {
          const sumWeights = values.reduce((acc, v) => acc + v.trust, 0);
          const weightedSum = values.reduce((acc, v) => acc + v.value * v.trust, 0);
          fused[field] = {
            value: weightedSum / (sumWeights || 1),
            confidence: sumWeights / values.length,
          };
        } else {
          const best = values.sort((a, b) => b.trust - a.trust)[0];
          fused[field] = { value: best.value, confidence: best.trust };
        }

        // Update trust based on deviation from consensus
        this.updateTrust(values, fused[field].value);
      }
    }

    return fused;
  }

  private trustScore(source: string): number {
    return this.sourceTrust.get(source) ?? 0.5;
  }

  private updateTrust(values: { source: string; value: any }[], consensus: any): void {
    values.forEach((v) => {
      const current = this.sourceTrust.get(v.source) ?? 0.5;
      let delta = 0;
      if (typeof v.value === "number" && typeof consensus === "number") {
        const deviation = Math.abs(v.value - consensus) / (Math.abs(consensus) + 1);
        delta = deviation < 0.1 ? 0.01 : -0.01;
      } else {
        delta = v.value === consensus ? 0.01 : -0.01;
      }
      this.sourceTrust.set(v.source, Math.min(1.0, Math.max(0.1, current + delta)));
    });
  }

  private computeFusionConfidence(data: DataPoint[]): number {
    return Math.min(1.0, data.length * 0.3);
  }
}
