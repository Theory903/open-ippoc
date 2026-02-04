import { CapabilityTokenManager } from "../execution/capability-tokens.js";

export class PermissionGates {
  constructor(private tokens: CapabilityTokenManager) {}

  checkGate(gate: string, token: string): boolean {
    const scopeMap: Record<string, string> = {
      CORE_UPDATE: "KERNEL",
      NETWORK_BIND: "NET",
      FS_WRITE_ROOT: "FS_WRITE",
      SHELL_SPAWN: "EXEC",
    };

    const requiredScope = scopeMap[gate];
    if (!requiredScope) {
      console.error(`[PermissionGates] Unknown gate: ${gate}`);
      return false;
    }

    // Dynamic import to avoid circular dep
    try {
      const { CapabilityScope } = require("../execution/capability-tokens.js");
      const hal = require("../index.js").HAL.getInstance();
      return hal.execution.tokens.verify(token, CapabilityScope[requiredScope]);
    } catch (e) {
      return false;
    }
  }
}
