import { hashes, getPublicKey } from "@noble/ed25519";
import { randomBytes, createHash } from "crypto";
import { describe, it, expect } from "vitest";
import { ReplayCache } from "./replay-cache.js";
import { SovereignHandshake } from "./sovereign-handshake.js";
import { TrustStateMachine, TrustLevel } from "./trust-state-machine.js";

// Configure sha512 for ed25519 in test environment
const sha512Polyfill = (m: Uint8Array): Uint8Array => {
  const hash = createHash("sha512");
  hash.update(m);
  return new Uint8Array(hash.digest());
};

hashes.sha512 = sha512Polyfill;
hashes.sha512Async = async (m) => sha512Polyfill(m);

describe("SovereignHandshake", () => {
  // Generate static keys for test speed
  it("should complete a full handshake", async () => {
    // Generate keys
    const privKey1 = randomBytes(32);
    const pubKey1 = await getPublicKey(privKey1);
    const privKey2 = randomBytes(32);
    const pubKey2 = await getPublicKey(privKey2);

    const trustMachine1 = new TrustStateMachine();
    const replayCache1 = new ReplayCache();
    const node1 = new SovereignHandshake({
      keypair: { privateKey: privKey1, publicKey: pubKey1 },
      trustMachine: trustMachine1,
      replayCache: replayCache1,
    });

    const trustMachine2 = new TrustStateMachine();
    const replayCache2 = new ReplayCache();
    const node2 = new SovereignHandshake({
      keypair: { privateKey: privKey2, publicKey: pubKey2 },
      trustMachine: trustMachine2,
      replayCache: replayCache2,
    });

    // 1. Node 1 initiates (SYN)
    const syn = await node1.initiate(pubKey2);

    // 2. Node 2 responds (SYN-ACK)
    const synack = await node2.respond(syn);

    // Check if Node 2 promoted Node 1
    expect(trustMachine2.getLevel(pubKey1)).toBe(TrustLevel.PROBATION);

    // 3. Node 1 completes (ACK)
    await node1.complete(synack);

    // Check if Node 1 promoted Node 2
    expect(trustMachine1.getLevel(pubKey2)).toBe(TrustLevel.PROBATION);
  });

  it("should prevent replay attacks", async () => {
    const privKey1 = randomBytes(32);
    const pubKey1 = await getPublicKey(privKey1);
    const privKey2 = randomBytes(32);
    const pubKey2 = await getPublicKey(privKey2);

    const trustMachine = new TrustStateMachine();
    const replayCache = new ReplayCache();
    const node = new SovereignHandshake({
      keypair: { privateKey: privKey1, publicKey: pubKey1 },
      trustMachine,
      replayCache,
    });

    const syn = await node.initiate(pubKey2);

    // Mock a response that successfully completes
    // In reality we just want to test "seen" logic on the initiate side if we were receiving,
    // but here let's test the 'respond' receiving a replayed SYN

    await node.respond(syn); // First time OK

    // Second time should fail
    await expect(node.respond(syn)).rejects.toThrow("Replay attack detected");
  });

  it("should reject invalid signatures", async () => {
    const privKey1 = randomBytes(32);
    const pubKey1 = await getPublicKey(privKey1);
    const privKey2 = randomBytes(32);
    const pubKey2 = await getPublicKey(privKey2);

    const trustMachine = new TrustStateMachine();
    const replayCache = new ReplayCache();
    const node = new SovereignHandshake({
      keypair: { privateKey: privKey1, publicKey: pubKey1 },
      trustMachine,
      replayCache,
    });

    const syn = await node.initiate(pubKey2);

    // Tamper with challenge (complement first byte)
    syn.challenge[0] ^= 0xff;

    await expect(node.respond(syn)).rejects.toThrow("Invalid challenge signature");
  });
});
