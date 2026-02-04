import { lookup as dnsLookupCb, type LookupAddress } from "node:dns";
import { lookup as dnsLookup } from "node:dns/promises";
import { Agent, type Dispatcher } from "undici";
import { getBrainClient, isBrainFeatureEnabled, getSecurityStrictness } from "../brain-config.js";

// Brain-powered SSRF protection using IPPOC Brain cognitive analysis

type LookupCallback = (
  err: NodeJS.ErrnoException | null,
  address: string | LookupAddress[],
  family?: number,
) => void;

export class BrainSsrFBlockedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BrainSsrFBlockedError";
  }
}

type LookupFn = typeof dnsLookup;

const PRIVATE_IPV6_PREFIXES = ["fe80:", "fec0:", "fc", "fd"];
const BLOCKED_HOSTNAMES = new Set(["localhost", "metadata.google.internal"]);

// Brain-powered hostname analysis
interface BrainSecurityAnalysis {
  risk_level: "low" | "medium" | "high" | "critical";
  confidence: number;
  reasoning: string;
  recommended_action: "allow" | "block" | "warn" | "investigate";
  threat_indicators: string[];
}

class BrainSecurityAnalyzer {
  private brainClient = getBrainClient();

  async analyzeHostname(hostname: string, context?: any): Promise<BrainSecurityAnalysis> {
    // Check if brain SSRF is enabled
    if (!isBrainFeatureEnabled("enableBrainSsrf")) {
      return this.fallbackAnalysis(hostname);
    }

    try {
      const result = await this.brainClient.invokeTool(
        "security",
        "security",
        "analyze_hostname_risk",
        {
          hostname,
          context_analysis: context || {},
          threat_intelligence_required: true,
          security_strictness: getSecurityStrictness(),
        },
        "medium",
      );

      if (result.success && result.output) {
        return result.output as BrainSecurityAnalysis;
      }
    } catch (error) {
      console.warn(`[Brain SSRF] Security analysis failed for ${hostname}:`, error);
    }

    // Fallback analysis
    return this.fallbackAnalysis(hostname);
  }

  private fallbackAnalysis(hostname: string): BrainSecurityAnalysis {
    const normalized = hostname.toLowerCase().trim();

    // Basic pattern matching for obvious threats
    const threatIndicators: string[] = [];

    if (normalized.includes("localhost") || normalized.includes("127.0.0.1")) {
      threatIndicators.push("local_access_attempt");
    }

    if (normalized.includes("metadata") || normalized.includes("internal")) {
      threatIndicators.push("metadata_service_access");
    }

    if (normalized.match(/^10\.|^172\.(1[6-9]|2[0-9]|3[01])\.|^192\.168\./)) {
      threatIndicators.push("private_network_access");
    }

    const riskLevel = threatIndicators.length > 0 ? "high" : "low";

    return {
      risk_level: riskLevel,
      confidence: threatIndicators.length > 0 ? 0.9 : 0.7,
      reasoning:
        threatIndicators.length > 0
          ? `Detected ${threatIndicators.join(", ")} threat indicators`
          : "No obvious threat patterns detected",
      recommended_action: threatIndicators.length > 0 ? "block" : "allow",
      threat_indicators: threatIndicators,
    };
  }
}

const brainAnalyzer = new BrainSecurityAnalyzer();

function normalizeHostname(hostname: string): string {
  const normalized = hostname.trim().toLowerCase().replace(/\.$/, "");
  if (normalized.startsWith("[") && normalized.endsWith("]")) {
    return normalized.slice(1, -1);
  }
  return normalized;
}

function parseIpv4(address: string): number[] | null {
  const parts = address.split(".");
  if (parts.length !== 4) {
    return null;
  }
  const numbers = parts.map((part) => Number.parseInt(part, 10));
  if (numbers.some((value) => Number.isNaN(value) || value < 0 || value > 255)) {
    return null;
  }
  return numbers;
}

function isPrivateIpv4(parts: number[]): boolean {
  const [octet1, octet2] = parts;
  if (octet1 === 0) return true;
  if (octet1 === 10) return true;
  if (octet1 === 127) return true;
  if (octet1 === 169 && octet2 === 254) return true;
  if (octet1 === 172 && octet2 >= 16 && octet2 <= 31) return true;
  if (octet1 === 192 && octet2 === 168) return true;
  if (octet1 === 100 && octet2 >= 64 && octet2 <= 127) return true;
  return false;
}

export async function isPrivateIpAddress(address: string): Promise<boolean> {
  let normalized = address.trim().toLowerCase();
  if (normalized.startsWith("[") && normalized.endsWith("]")) {
    normalized = normalized.slice(1, -1);
  }
  if (!normalized) {
    return false;
  }

  // Use brain analysis for sophisticated private IP detection
  const brainAnalysis = await brainAnalyzer.analyzeHostname(normalized, {
    ip_address_analysis: true,
    private_network_detection: true,
  });

  if (brainAnalysis.risk_level === "high" && brainAnalysis.recommended_action === "block") {
    return true;
  }

  // Fallback to traditional detection
  if (normalized.startsWith("::ffff:")) {
    const mapped = normalized.slice("::ffff:".length);
    const ipv4 = parseIpv4(mapped);
    if (ipv4) {
      return isPrivateIpv4(ipv4);
    }
  }

  if (normalized.includes(":")) {
    if (normalized === "::" || normalized === "::1") {
      return true;
    }
    return PRIVATE_IPV6_PREFIXES.some((prefix) => normalized.startsWith(prefix));
  }

  const ipv4 = parseIpv4(normalized);
  if (!ipv4) {
    return false;
  }
  return isPrivateIpv4(ipv4);
}

export async function isBlockedHostname(hostname: string): Promise<boolean> {
  const normalized = normalizeHostname(hostname);
  if (!normalized) {
    return false;
  }

  // Brain-powered hostname analysis
  const brainAnalysis = await brainAnalyzer.analyzeHostname(normalized, {
    hostname_blocking_check: true,
    context: "ssrf_protection",
  });

  if (brainAnalysis.recommended_action === "block") {
    console.log(`[Brain SSRF] Blocking hostname ${hostname}: ${brainAnalysis.reasoning}`);
    return true;
  }

  // Fallback to traditional blocked hostnames
  if (BLOCKED_HOSTNAMES.has(normalized)) {
    return true;
  }

  return (
    normalized.endsWith(".localhost") ||
    normalized.endsWith(".local") ||
    normalized.endsWith(".internal")
  );
}

export async function createPinnedLookup(params: {
  hostname: string;
  addresses: string[];
  fallback?: typeof dnsLookupCb;
}): Promise<typeof dnsLookupCb> {
  const normalizedHost = normalizeHostname(params.hostname);
  const fallback = params.fallback ?? dnsLookupCb;
  const fallbackLookup = fallback as unknown as (
    hostname: string,
    callback: LookupCallback,
  ) => void;
  const fallbackWithOptions = fallback as unknown as (
    hostname: string,
    options: unknown,
    callback: LookupCallback,
  ) => void;
  const records = params.addresses.map((address) => ({
    address,
    family: address.includes(":") ? 6 : 4,
  }));
  let index = 0;

  return ((host: string, options?: unknown, callback?: unknown) => {
    const cb: LookupCallback =
      typeof options === "function" ? (options as LookupCallback) : (callback as LookupCallback);
    if (!cb) {
      return;
    }
    const normalized = normalizeHostname(host);
    if (!normalized || normalized !== normalizedHost) {
      if (typeof options === "function" || options === undefined) {
        return fallbackLookup(host, cb);
      }
      return fallbackWithOptions(host, options, cb);
    }

    const opts =
      typeof options === "object" && options !== null
        ? (options as { all?: boolean; family?: number })
        : {};
    const requestedFamily =
      typeof options === "number" ? options : typeof opts.family === "number" ? opts.family : 0;
    const candidates =
      requestedFamily === 4 || requestedFamily === 6
        ? records.filter((entry) => entry.family === requestedFamily)
        : records;
    const usable = candidates.length > 0 ? candidates : records;
    if (opts.all) {
      cb(null, usable as LookupAddress[]);
      return;
    }
    const chosen = usable[index % usable.length];
    index += 1;
    cb(null, chosen.address, chosen.family);
  }) as typeof dnsLookupCb;
}

export interface BrainPinnedHostname {
  hostname: string;
  addresses: string[];
  lookup: typeof dnsLookupCb;
  security_analysis: BrainSecurityAnalysis;
}

export async function resolvePinnedHostname(
  hostname: string,
  lookupFn: LookupFn = dnsLookup,
): Promise<BrainPinnedHostname> {
  const normalized = normalizeHostname(hostname);
  if (!normalized) {
    throw new Error("Invalid hostname");
  }

  // Brain-powered security analysis
  const securityAnalysis = await brainAnalyzer.analyzeHostname(normalized, {
    dns_resolution_context: true,
    ssrf_protection: true,
  });

  if (securityAnalysis.recommended_action === "block") {
    throw new BrainSsrFBlockedError(
      `Brain-blocked hostname: ${hostname} - ${securityAnalysis.reasoning}`,
    );
  }

  if (await isPrivateIpAddress(normalized)) {
    throw new BrainSsrFBlockedError("Brain-blocked: private/internal IP address");
  }

  const results = await lookupFn(normalized, { all: true });
  if (results.length === 0) {
    throw new Error(`Unable to resolve hostname: ${hostname}`);
  }

  // Analyze each resolved address
  for (const entry of results) {
    if (await isPrivateIpAddress(entry.address)) {
      throw new BrainSsrFBlockedError("Brain-blocked: resolves to private/internal IP address");
    }
  }

  const addresses = Array.from(new Set(results.map((entry) => entry.address)));
  if (addresses.length === 0) {
    throw new Error(`Unable to resolve hostname: ${hostname}`);
  }

  const lookup = await createPinnedLookup({ hostname: normalized, addresses });

  return {
    hostname: normalized,
    addresses,
    lookup,
    security_analysis: securityAnalysis,
  };
}

export function createPinnedDispatcher(pinned: BrainPinnedHostname): Dispatcher {
  return new Agent({
    connect: {
      lookup: pinned.lookup,
    },
  });
}

export async function closeDispatcher(dispatcher?: Dispatcher | null): Promise<void> {
  if (!dispatcher) {
    return;
  }
  const candidate = dispatcher as { close?: () => Promise<void> | void; destroy?: () => void };
  try {
    if (typeof candidate.close === "function") {
      await candidate.close();
      return;
    }
    if (typeof candidate.destroy === "function") {
      candidate.destroy();
    }
  } catch {
    // ignore dispatcher cleanup errors
  }
}

export async function assertPublicHostname(
  hostname: string,
  lookupFn: LookupFn = dnsLookup,
): Promise<void> {
  await resolvePinnedHostname(hostname, lookupFn);
}
