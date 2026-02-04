export enum TrustLevel {
  NEW = "NEW", // Never seen before
  PROBATION = "PROBATION", // Handshake completed, limited privileges
  TRUSTED = "TRUSTED", // Proven track record, full privileges
  DROP = "DROP", // Explicitly untrusted/blocked
}

export class TrustStateMachine {
  private state = new Map<string, TrustLevel>();
  private successCounts = new Map<string, number>();

  getLevel(peerKey: Uint8Array): TrustLevel {
    const keyStr = Buffer.from(peerKey).toString("hex");
    return this.state.get(keyStr) ?? TrustLevel.NEW;
  }

  promote(peerKey: Uint8Array): void {
    const keyStr = Buffer.from(peerKey).toString("hex");
    const current = this.getLevel(peerKey);

    if (current === TrustLevel.NEW) {
      this.state.set(keyStr, TrustLevel.PROBATION);
      console.log(`[TrustStateMachine] Peer ${keyStr.slice(0, 8)} promoted to PROBATION`);
    } else if (current === TrustLevel.PROBATION) {
      const successes = (this.successCounts.get(keyStr) ?? 0) + 1;
      this.successCounts.set(keyStr, successes);

      if (successes >= 10) {
        // Require 10 successful interactions
        this.state.set(keyStr, TrustLevel.TRUSTED);
        console.log(`[TrustStateMachine] Peer ${keyStr.slice(0, 8)} promoted to TRUSTED`);
      }
    }
  }

  shouldDropPacket(peerKey: Uint8Array, packetType: string): boolean {
    const level = this.getLevel(peerKey);

    // NEW peers can only send handshake packets
    if (level === TrustLevel.NEW && packetType !== "SYN") return true;

    // PROBATION peers have limited packet types
    if (level === TrustLevel.PROBATION && !["SYN-ACK", "HEARTBEAT", "QUERY"].includes(packetType))
      return true;

    return false;
  }

  // --- Public Interface for Event Handler ---

  getTrust(peerId: string): TrustLevel {
    // In prod, this would look up by Key, but here we support string IDs
    // by hashing or lookup. For now, defaulting to NEW if unknown.
    return this.state.get(peerId) ?? TrustLevel.NEW;
  }

  interact(peerId: string, context: string, success: boolean): void {
    if (success) {
      const successes = (this.successCounts.get(peerId) ?? 0) + 1;
      this.successCounts.set(peerId, successes);

      if (successes >= 10 && this.getTrust(peerId) !== TrustLevel.TRUSTED) {
        this.state.set(peerId, TrustLevel.TRUSTED);
        console.log(`[TrustStateMachine] Peer ${peerId} promoted to TRUSTED`);
      }
    } else {
      // Demote on failure
      this.state.set(peerId, TrustLevel.NEW);
      this.successCounts.set(peerId, 0);
    }
  }
}
