export interface MarketSignal {
  source: "USER_FEEDBACK" | "SOCIAL_MEDIA" | "COMPETITOR_RELEASE";
  content: string;
  sentiment: number; // -1 to 1
  timestamp: number;
}

export interface FeatureGap {
  description: string;
  demandScore: number;
  urgency: "HIGH" | "MEDIUM" | "LOW";
  monetizationPotential: number; // 0-1
}

export class MarketSensing {
  private signals: MarketSignal[] = [];

  recordSignal(signal: MarketSignal): void {
    this.signals.push(signal);
    // Keep only last 1000 signals
    if (this.signals.length > 1000) {
      this.signals.shift();
    }
  }

  async analyzeTrends(): Promise<FeatureGap[]> {
    const gaps: FeatureGap[] = [];

    // 1. Analyze User Frustration (Sentiment < -0.5)
    const frustrationSignals = this.signals.filter((s) => s.sentiment < -0.5);

    // Cluster frustration signals by simple text similarity (Jaccard)
    if (frustrationSignals.length > 5) {
      const topIssue = this.findDominantTopic(frustrationSignals.map((s) => s.content));
      gaps.push({
        description: `High frustration detected: ${topIssue}`,
        demandScore: frustrationSignals.length,
        urgency: "HIGH",
        monetizationPotential: 0.8,
      });
    }

    // 2. Analyze Competitor Moves
    const compSignals = this.signals.filter((s) => s.source === "COMPETITOR_RELEASE");
    for (const signal of compSignals) {
      gaps.push({
        description: `Competitor Update: ${signal.content}`,
        demandScore: 50, // Default baseline
        urgency: "MEDIUM",
        monetizationPotential: 0.6,
      });
    }

    return gaps;
  }

  private findDominantTopic(texts: string[]): string {
    const words = texts.join(" ").split(/\s+/);
    const freq = new Map<string, number>();
    let maxFs = 0;
    let topic = "General Instability";

    for (const w of words) {
      if (w.length < 4) continue;
      const c = (freq.get(w) || 0) + 1;
      freq.set(w, c);
      if (c > maxFs) {
        maxFs = c;
        topic = w;
      }
    }
    return `${topic} issues`;
  }
}
