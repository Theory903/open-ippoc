import { randomBytes } from "crypto";
import { describe, it, expect } from "vitest";
import { CapabilityTokenManager, CapabilityScope } from "./capability-tokens";

describe("CapabilityTokenManager", () => {
  it("should issue and verify a valid token", () => {
    const manager = new CapabilityTokenManager();
    const token = manager.issue(CapabilityScope.FS_READ, 5000, "BRAIN");

    expect(token).toBeDefined();
    expect(token.scope).toBe(CapabilityScope.FS_READ);

    const isValid = manager.verify(token.id, CapabilityScope.FS_READ);
    expect(isValid).toBe(true);
  });

  it("should reject expired tokens", async () => {
    const manager = new CapabilityTokenManager();
    const token = manager.issue(CapabilityScope.NET_HTTP, 10, "BODY"); // 10ms TTL

    await new Promise((resolve) => setTimeout(resolve, 20));

    const isValid = manager.verify(token.id, CapabilityScope.NET_HTTP);
    expect(isValid).toBe(false);
  });

  it("should reject tokens with wrong scope", () => {
    const manager = new CapabilityTokenManager();
    const token = manager.issue(CapabilityScope.KERNEL, 5000, "BRAIN");

    const isValid = manager.verify(token.id, CapabilityScope.GPU);
    expect(isValid).toBe(false);
  });

  it("should enforce path constraints", () => {
    const manager = new CapabilityTokenManager();
    const token = manager.issue(CapabilityScope.FS_WRITE, 5000, "BRAIN", "/var/ippoc/safe");

    expect(manager.verify(token.id, CapabilityScope.FS_WRITE, "/var/ippoc/safe/log.txt")).toBe(
      true,
    );
    expect(manager.verify(token.id, CapabilityScope.FS_WRITE, "/etc/passwd")).toBe(false);
  });

  it("should prevent token reuse (replay)", () => {
    const manager = new CapabilityTokenManager();
    const token = manager.issue(CapabilityScope.WASM_EXEC, 5000, "BODY");

    expect(manager.verify(token.id, CapabilityScope.WASM_EXEC)).toBe(true);
    expect(manager.verify(token.id, CapabilityScope.WASM_EXEC)).toBe(false);
  });
});
