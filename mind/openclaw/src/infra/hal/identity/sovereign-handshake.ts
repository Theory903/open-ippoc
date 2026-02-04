import { sign, verify, hashes } from "@noble/ed25519";
import { randomUUID, createHash } from "crypto";
import { ReplayCache } from "./replay-cache.js";
import { TrustStateMachine } from "./trust-state-machine.js";

// Configure sha512 for ed25519
const sha512Polyfill = (m: Uint8Array): Uint8Array => {
  const hash = createHash("sha512");
  hash.update(m);
  return new Uint8Array(hash.digest());
};

hashes.sha512 = sha512Polyfill;

export interface HandshakeConfig {
  keypair: { privateKey: Uint8Array; publicKey: Uint8Array };
  trustMachine: TrustStateMachine;
  replayCache: ReplayCache;
}

export interface SYNPacket {
  type: "SYN";
  nonce: string;
  challenge: Uint8Array;
  publicKey: Uint8Array;
}

export interface SYNACKPacket {
  type: "SYN-ACK";
  nonce: string;
  challenge: Uint8Array;
  publicKey: Uint8Array;
}

export class SovereignHandshake {
  constructor(private config: HandshakeConfig) {}

  // SYN: Initiate handshake with challenge
  async initiate(peerPublicKey: Uint8Array): Promise<SYNPacket> {
    const nonce = randomUUID();
    const challenge = await sign(Buffer.from(nonce), this.config.keypair.privateKey);
    return { type: "SYN", nonce, challenge, publicKey: this.config.keypair.publicKey };
  }

  // SYN-ACK: Respond to challenge
  async respond(syn: SYNPacket): Promise<SYNACKPacket> {
    if (this.config.replayCache.seen(syn.nonce)) {
      throw new Error("Replay attack detected");
    }

    const verified = await verify(syn.challenge, Buffer.from(syn.nonce), syn.publicKey);
    if (!verified) throw new Error("Invalid challenge signature");

    const responseNonce = randomUUID();
    const responseChallenge = await sign(
      Buffer.from(responseNonce),
      this.config.keypair.privateKey,
    );

    this.config.replayCache.mark(syn.nonce);

    // Promote sender to Probation if valid
    this.config.trustMachine.promote(syn.publicKey);

    return {
      type: "SYN-ACK",
      nonce: responseNonce,
      challenge: responseChallenge,
      publicKey: this.config.keypair.publicKey,
    };
  }

  // ACK: Complete handshake (Verification of reply)
  async complete(synack: SYNACKPacket): Promise<void> {
    if (this.config.replayCache.seen(synack.nonce)) {
      throw new Error("Replay attack detected");
    }

    const verified = await verify(synack.challenge, Buffer.from(synack.nonce), synack.publicKey);
    if (!verified) throw new Error("Invalid response signature");

    this.config.trustMachine.promote(synack.publicKey);
    this.config.replayCache.mark(synack.nonce);
  }
}
