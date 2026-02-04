export type ModelWeights = Record<string, number[]>;

export interface NetworkTransport {
  broadcast(model: ModelWeights): Promise<void>;
  collect(timeoutMs: number): Promise<ModelWeights[]>;
}

class LocalLoopbackTransport implements NetworkTransport {
  constructor(
    private participants: Set<string>,
    private globalModel: ModelWeights,
  ) {}

  async broadcast(model: ModelWeights): Promise<void> {
    // In loopback, we just optimize locally
  }

  async collect(timeoutMs: number): Promise<ModelWeights[]> {
    // Simulate local participants training on their own data
    return Array.from(this.participants).map(() => {
      const updates: ModelWeights = {};
      for (const k in this.globalModel) {
        updates[k] = this.globalModel[k].map((w) => w + (Math.random() - 0.5) * 0.01);
      }
      return updates;
    });
  }
}

export class FederatedLearning {
  private globalModel: ModelWeights = {};
  private participants: Set<string> = new Set();
  private transport: NetworkTransport;

  constructor(initialUnusedWeights?: ModelWeights) {
    this.globalModel = initialUnusedWeights || { layer1: [0.1, 0.2], layer2: [0.5, -0.1] };
    // Default to loopback until network module is injected
    this.transport = new LocalLoopbackTransport(this.participants, this.globalModel);
  }

  async registerParticipant(id: string): Promise<void> {
    this.participants.add(id);
    // Re-init transport to include new participant
    this.transport = new LocalLoopbackTransport(this.participants, this.globalModel);
    console.log(`[Federated] Participant ${id} registered.`);
  }

  async federatedTrain(rounds: number): Promise<void> {
    for (let round = 0; round < rounds; round++) {
      console.log(`[Federated] Round ${round + 1}/${rounds} starting...`);

      // 1. Distribute Model
      await this.transport.broadcast(this.globalModel);

      // 2. Collect Updates
      const updates = await this.transport.collect(5000);

      // 3. Aggregate
      this.globalModel = this.aggregateModels(updates);

      console.log(`[Federated] Round ${round + 1} complete. Model updated.`);
    }
  }

  private aggregateModels(models: ModelWeights[]): ModelWeights {
    const keys = Object.keys(this.globalModel);
    const aggregated: ModelWeights = {};

    for (const key of keys) {
      const layerWeights = models.map((m) => m[key]);
      // FedAvg: Average weights
      aggregated[key] = layerWeights[0].map(
        (_, i) => layerWeights.reduce((sum, w) => sum + w[i], 0) / models.length,
      );
    }
    return aggregated;
  }
}
