import { randomBytes, createHash } from "crypto";

export enum CapabilityScope {
  // Basic scopes
  FS_READ = "FS_READ",
  FS_WRITE = "FS_WRITE",
  NET_HTTP = "NET_HTTP",
  NET_SOCKET = "NET_SOCKET",
  KERNEL = "KERNEL",
  GPU = "GPU",
  WASM_EXEC = "WASM_EXEC",
  EXEC = "EXEC",

  // Hierarchical admin scopes
  ADMIN = "ADMIN",
  NODE_LOCAL = "NODE_LOCAL",
  CROSS_NODE = "CROSS_NODE",
  SECURITY = "SECURITY",
  EVOLUTION = "EVOLUTION",

  // Specialized scopes
  MEMORY_MANAGE = "MEMORY_MANAGE",
  NETWORK_CONFIG = "NETWORK_CONFIG",
  RESOURCE_QUOTA = "RESOURCE_QUOTA",
  AUDIT_LOG = "AUDIT_LOG",
  DEBUG_ATTACH = "DEBUG_ATTACH",

  // Temporary scopes
  TEMPORARY = "TEMPORARY",
  EMERGENCY = "EMERGENCY",
  MAINTENANCE = "MAINTENANCE",
}

export interface CapabilityToken {
  id: string;
  scope: CapabilityScope;
  ttl_ms: number;
  issued_by: "BRAIN" | "BODY" | "HAL_ADMIN" | "SECURITY_MODULE";
  issued_at: number;
  expires_at: number;
  path_constraint?: string;
  domain_constraint?: string;
  resource_limits?: ResourceLimits;
  audit_trail: AuditRecord[];
  revocation_reason?: string;
  parent_token?: string;
  signature: string;
  checksum: string;
}

export interface ResourceLimits {
  cpu_cores?: number;
  memory_mb?: number;
  gpu_units?: number;
  network_bandwidth_mbps?: number;
  execution_timeout_ms?: number;
  max_concurrent_operations?: number;
}

export interface AuditRecord {
  timestamp: number;
  action: string;
  resource: string;
  success: boolean;
  metadata?: Record<string, any>;
}

export class CapabilityTokenManager {
  private tokens = new Map<string, CapabilityToken>();
  private usedTokens = new Set<string>();
  private revokedTokens = new Map<string, string>();
  private tokenHierarchy = new Map<string, string[]>();
  private securityModuleKey: string;

  constructor(securityModuleKey?: string) {
    this.securityModuleKey = securityModuleKey || this.generateMasterKey();
  }

  private generateMasterKey(): string {
    return randomBytes(32).toString("hex");
  }

  issue(params: {
    scope: CapabilityScope;
    ttl_ms: number;
    issuer: "BRAIN" | "BODY" | "HAL_ADMIN" | "SECURITY_MODULE";
    pathConstraint?: string;
    domainConstraint?: string;
    resourceLimits?: ResourceLimits;
    parentId?: string;
    emergency?: boolean;
  }): CapabilityToken {
    const {
      scope,
      ttl_ms,
      issuer,
      pathConstraint,
      domainConstraint,
      resourceLimits,
      parentId,
      emergency = false,
    } = params;

    const now = Date.now();
    const token: CapabilityToken = {
      id: randomBytes(16).toString("hex"),
      scope,
      ttl_ms,
      issued_by: issuer,
      issued_at: now,
      expires_at: now + ttl_ms,
      path_constraint: pathConstraint,
      domain_constraint: domainConstraint,
      resource_limits: resourceLimits,
      audit_trail: [],
      parent_token: parentId,
      signature: this.signToken({
        scope,
        ttl_ms,
        issuer,
        pathConstraint,
        domainConstraint,
      }),
      checksum: this.computeChecksum({
        scope,
        issuer,
        issued_at: now,
        expires_at: now + ttl_ms,
      }),
    };

    if (emergency) {
      token.audit_trail.push({
        timestamp: now,
        action: "TOKEN_ISSUED_EMERGENCY",
        resource: "SYSTEM",
        success: true,
        metadata: { reason: "Emergency access granted" },
      });
    }

    this.tokens.set(token.id, token);

    if (parentId) {
      if (!this.tokenHierarchy.has(parentId)) {
        this.tokenHierarchy.set(parentId, []);
      }
      this.tokenHierarchy.get(parentId)!.push(token.id);
    }

    return token;
  }

  verify(
    tokenId: string,
    requiredScope: CapabilityScope,
    params?: {
      path?: string;
      domain?: string;
      resourceAction?: string;
      emergencyOverride?: boolean;
    },
  ): { valid: boolean; reason?: string; token?: CapabilityToken } {
    const { path, domain, resourceAction, emergencyOverride = false } = params || {};

    if (this.revokedTokens.has(tokenId)) {
      return {
        valid: false,
        reason: `Token revoked: ${this.revokedTokens.get(tokenId)}`,
      };
    }

    const token = this.tokens.get(tokenId);
    if (!token) {
      return { valid: false, reason: "Token not found" };
    }

    const now = Date.now();

    if (now > token.expires_at) {
      this.tokens.delete(tokenId);
      return { valid: false, reason: "Token expired" };
    }

    const isEmergency = token.scope === CapabilityScope.EMERGENCY || emergencyOverride;

    if (!this.isScopeAuthorized(token.scope, requiredScope) && !isEmergency) {
      return {
        valid: false,
        reason: `Insufficient scope: ${token.scope} cannot access ${requiredScope}`,
      };
    }

    if (token.path_constraint && path && !path.startsWith(token.path_constraint)) {
      return { valid: false, reason: `Path constraint violation` };
    }

    if (token.domain_constraint && domain && domain !== token.domain_constraint) {
      return { valid: false, reason: `Domain constraint violation` };
    }

    token.audit_trail.push({
      timestamp: now,
      action: resourceAction || "TOKEN_VERIFICATION",
      resource: path || domain || "SYSTEM",
      success: true,
    });

    if (this.isSingleUseScope(token.scope)) {
      this.usedTokens.add(tokenId);
    }

    return { valid: true, token };
  }

  private signToken(payload: any): string {
    const dataToSign = JSON.stringify({
      ...payload,
      security_module: "HAL_EXECUTION",
      timestamp: Date.now(),
    });

    return createHash("sha256").update(dataToSign).update(this.securityModuleKey).digest("hex");
  }

  private computeChecksum(payload: any): string {
    return createHash("sha1").update(JSON.stringify(payload)).digest("hex");
  }

  private isScopeAuthorized(tokenScope: CapabilityScope, requiredScope: CapabilityScope): boolean {
    if (tokenScope === CapabilityScope.ADMIN) return true;
    if (tokenScope === CapabilityScope.SECURITY) return true;
    if (tokenScope === requiredScope) return true;

    const hierarchy: Partial<Record<CapabilityScope, CapabilityScope[]>> = {
      [CapabilityScope.ADMIN]: Object.values(CapabilityScope),
      [CapabilityScope.NODE_LOCAL]: [
        CapabilityScope.FS_READ,
        CapabilityScope.FS_WRITE,
        CapabilityScope.EXEC,
        CapabilityScope.WASM_EXEC,
      ],
      [CapabilityScope.CROSS_NODE]: [
        CapabilityScope.NET_HTTP,
        CapabilityScope.NET_SOCKET,
        CapabilityScope.MEMORY_MANAGE,
      ],
    };

    return hierarchy[tokenScope]?.includes(requiredScope) || false;
  }

  private isSingleUseScope(scope: CapabilityScope): boolean {
    return [
      CapabilityScope.TEMPORARY,
      CapabilityScope.EMERGENCY,
      CapabilityScope.MAINTENANCE,
    ].includes(scope);
  }

  revoke(tokenId: string, reason: string): boolean {
    const token = this.tokens.get(tokenId);
    if (!token) return false;

    this.revokedTokens.set(tokenId, reason);
    this.tokens.delete(tokenId);

    const children = this.tokenHierarchy.get(tokenId) || [];
    for (const childId of children) {
      this.revoke(childId, `Parent token revoked: ${reason}`);
    }

    token.audit_trail.push({
      timestamp: Date.now(),
      action: "TOKEN_REVOKED",
      resource: "SYSTEM",
      success: true,
      metadata: { reason },
    });

    return true;
  }

  getAuditTrail(tokenId: string): AuditRecord[] {
    const token = this.tokens.get(tokenId);
    return token ? [...token.audit_trail] : [];
  }

  getTokenStats(): any {
    return {
      total_tokens: this.tokens.size + this.revokedTokens.size,
      active_tokens: this.tokens.size,
      revoked_tokens: this.revokedTokens.size,
      used_tokens: this.usedTokens.size,
    };
  }
}
