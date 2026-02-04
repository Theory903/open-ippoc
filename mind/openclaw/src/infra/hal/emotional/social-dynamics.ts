export interface SocialDynamics {
  participants: string[];
  roles: Map<string, string>;
  cohesion: number;
}

export class SocialDynamicsAnalyzer {
  async analyzeGroup(conversation: { sender: string; content: string }[]): Promise<SocialDynamics> {
    const participants = Array.from(new Set(conversation.map((m) => m.sender)));
    const roles = new Map<string, string>();

    // Simple role assignment
    participants.forEach((p) => {
      const msgCount = conversation.filter((m) => m.sender === p).length;
      if (msgCount > conversation.length / 2) {
        roles.set(p, "LEADER");
      } else {
        roles.set(p, "PARTICIPANT");
      }
    });

    return {
      participants,
      roles,
      cohesion: 0.8, // Placeholder metric
    };
  }
}
