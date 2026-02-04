import { describe, it, expect } from "vitest";
import { CapabilityTokenManager, CapabilityScope } from "./capability-tokens.js";
import { WASMGate } from "./wasm-gate.js";

describe("WASMGate", () => {
  it("should block execution without valid tokens", async () => {
    const tokenManager = new CapabilityTokenManager();
    const gate = new WASMGate(tokenManager);

    // Simple WASM module (empty)
    const wasmCode = new Uint8Array([0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00]);

    await expect(
      gate.executeWASM(wasmCode, [CapabilityScope.WASM_EXEC], ["invalid-token"]),
    ).rejects.toThrow("Missing or invalid token");
  });

  it("should execute WASM with valid tokens", async () => {
    const tokenManager = new CapabilityTokenManager();
    const gate = new WASMGate(tokenManager);

    const token = tokenManager.issue(CapabilityScope.WASM_EXEC, 5000, "BRAIN");

    // Simple WASM module (valid header)
    const wasmCode = new Uint8Array([0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00]);

    const exports = await gate.executeWASM(wasmCode, [CapabilityScope.WASM_EXEC], [token.id]);

    expect(exports).toBeDefined();
  });
});
