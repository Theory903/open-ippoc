import { CapabilityTokenManager, CapabilityScope } from "./capability-tokens.js";

export class WASMGate {
  constructor(private tokenManager: CapabilityTokenManager) {}

  async executeWASM(
    wasmCode: Uint8Array,
    requiredCapabilities: CapabilityScope[],
    tokens: string[],
  ): Promise<any> {
    // Verify all required tokens
    for (let i = 0; i < requiredCapabilities.length; i++) {
      const scope = requiredCapabilities[i];
      const tokenId = tokens[i];

      if (!this.tokenManager.verify(tokenId, scope)) {
        throw new Error(`Missing or invalid token for capability: ${scope}`);
      }
    }

    // Execute WASM in isolated context
    const module = await WebAssembly.compile(wasmCode);
    const instance = await WebAssembly.instantiate(module, this.createSandbox());

    return instance.exports;
  }

  private createSandbox(): WebAssembly.Imports {
    // Provide only minimal, safe imports
    return {
      env: {
        memory: new WebAssembly.Memory({ initial: 256, maximum: 512 }),
        abort: () => {
          throw new Error("WASM abort");
        },
      },
    };
  }
}
