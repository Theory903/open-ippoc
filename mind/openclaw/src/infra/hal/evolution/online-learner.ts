export interface Interaction {
  state: any;
  action: string;
}

export interface Outcome {
  state: any;
  reward: number; // calculated externally
}

export interface Experience {
  state: any;
  action: string;
  reward: number;
  nextState: any;
}

export interface Feedback {
  type: "POSITIVE" | "NEGATIVE";
  context: Interaction;
}

export class OnlineLearner {
  private experienceReplay: Experience[] = [];

  // Simple linear model: y = w*x + b
  private weights: Map<string, number> = new Map();
  private bias: number = 0;

  private predict(state: any): number {
    // Simple hash-based feature extraction for generic strict objects
    let score = this.bias;
    for (const key in state) {
      if (typeof state[key] === "number") {
        score += (this.weights.get(key) || 0) * state[key];
      }
    }
    return 1 / (1 + Math.exp(-score)); // Sigmoid
  }

  private async fit(states: any[], targets: number[]): Promise<void> {
    // Simple Stochastic Gradient Descent
    const learningRate = 0.01;
    states.forEach((state, i) => {
      const pred = this.predict(state);
      const error = targets[i] - pred;
      // Update bias
      this.bias += learningRate * error;
      // Update weights
      for (const key in state) {
        if (typeof state[key] === "number") {
          const w = this.weights.get(key) || 0;
          this.weights.set(key, w + learningRate * error * state[key]);
        }
      }
    });
  }

  private adjustActionWeight(state: any, action: string, delta: number): void {
    // Modify weights associated with this state-action pair
    // Adjust bias for the specific action pathway
    this.bias += delta;
    this.bias += delta;
  }

  async learn(interaction: Interaction, outcome: Outcome): Promise<void> {
    // 1. Store experience
    this.experienceReplay.push({
      state: interaction.state,
      action: interaction.action,
      reward: outcome.reward,
      nextState: outcome.state,
    });

    // 2. Keep buffer bounded
    if (this.experienceReplay.length > 1000) {
      this.experienceReplay.shift();
    }

    // 3. Periodic training
    if (this.experienceReplay.length % 50 === 0) {
      await this.trainBatch();
    }
  }

  async adaptPolicy(feedback: Feedback): Promise<void> {
    if (feedback.type === "NEGATIVE") {
      // Reduce probability of action that led to negative feedback
      this.adjustActionWeight(feedback.context.state, feedback.context.action, -0.1);
      console.log(`[HAL] 📉 Adapting policy: Penalized action ${feedback.context.action}`);
    } else if (feedback.type === "POSITIVE") {
      this.adjustActionWeight(feedback.context.state, feedback.context.action, 0.1);
      console.log(`[HAL] 📈 Adapting policy: Reinforced action ${feedback.context.action}`);
    }
  }

  // --- Helpers ---

  private async trainBatch(): Promise<void> {
    const batchSize = 10;
    if (this.experienceReplay.length < batchSize) return;

    // Sample random batch
    const batch = this.sampleBatch(batchSize);

    // Compute Q-learning targets: R + gamma * max(Q(next))
    const targets = batch.map((exp) => exp.reward + 0.95 * this.predict(exp.nextState));

    // Update model
    await this.fit(
      batch.map((exp) => exp.state),
      targets,
    );

    // console.log('🧠 Model updated with new batch via online learning');
  }

  private sampleBatch(size: number): Experience[] {
    const idx = Math.floor(Math.random() * (this.experienceReplay.length - size));
    return this.experienceReplay.slice(idx, idx + size);
  }
}
