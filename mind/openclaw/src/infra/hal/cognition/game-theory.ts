export interface Agent {
  id: string;
  role: string;
}

export interface GameDefinition {
  players: string[];
  actions: string[];
  payoffFunction: (actions: Record<string, string>) => Record<string, number>;
}

export interface Strategy {
  action: string;
  expectedOutcome: any;
  reasoning: string;
}

export interface AgentModel {
  agentId: string;
  rationalityLevel: number; // 0-1
}

interface Equilibrium {
  strategies: Record<string, string>;
  stable: boolean;
}

export class GameTheoreticPlanner {
  async planStrategy(
    agents: Agent[],
    game: GameDefinition,
    myRole: string, // Agent ID
  ): Promise<Strategy> {
    // 1. Model other agents
    const agentModels = await Promise.all(agents.map((a) => this.modelAgent(a)));

    // 2. Find Nash equilibrium
    const equilibria = this.findNashEquilibria(agents, game);

    const bestEquilibrium = equilibria[0]; // Simplification

    if (!bestEquilibrium) {
      return {
        action: game.actions[0],
        expectedOutcome: "Fallback",
        reasoning: "No clear equilibrium found, taking safe default.",
      };
    }

    const myAction = bestEquilibrium.strategies[myRole];

    return {
      action: myAction,
      expectedOutcome: game.payoffFunction(bestEquilibrium.strategies),
      reasoning: `Nash Equilibrium reached at ${JSON.stringify(bestEquilibrium.strategies)}. Deviation decreases utility.`,
    };
  }

  private async modelAgent(agent: Agent): Promise<AgentModel> {
    return {
      agentId: agent.id,
      rationalityLevel: 0.9, // Assume rational actors
    };
  }

  private findNashEquilibria(agents: Agent[], game: GameDefinition): Equilibrium[] {
    const equilibria: Equilibrium[] = [];
    // Brute force pure strategy search (sufficient for small N games)
    const profiles = this.generateStrategyProfiles(agents, game.actions);

    for (const profile of profiles) {
      if (this.isNashEquilibrium(profile, agents, game)) {
        equilibria.push({ strategies: profile, stable: true });
      }
    }

    return equilibria;
  }

  private isNashEquilibrium(
    profile: Record<string, string>,
    agents: Agent[],
    game: GameDefinition,
  ): boolean {
    for (const agent of agents) {
      const currentPayoff = game.payoffFunction(profile)[agent.id];

      // Check deviations
      for (const altAction of game.actions) {
        if (altAction === profile[agent.id]) continue;

        const deviatedProfile = { ...profile, [agent.id]: altAction };
        const deviatedPayoff = game.payoffFunction(deviatedProfile)[agent.id];

        if (deviatedPayoff > currentPayoff) {
          return false; // Agent can improve by deviating
        }
      }
    }
    return true;
  }

  private generateStrategyProfiles(agents: Agent[], actions: string[]): Record<string, string>[] {
    // Recursive generation of full cartesian product of strategies
    if (agents.length === 0) return [{}];

    const firstAgent = agents[0];
    const restAgents = agents.slice(1);
    const subProfiles = this.generateStrategyProfiles(restAgents, actions);

    const profiles: Record<string, string>[] = [];
    for (const action of actions) {
      for (const sub of subProfiles) {
        profiles.push({ [firstAgent.id]: action, ...sub });
      }
    }
    return profiles;
  }
}
