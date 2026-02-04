// Brain-powered TLS fingerprinting and security analysis

interface TlsFingerprintAnalysis {
  fingerprint: string;
  security_rating: "excellent" | "good" | "fair" | "poor" | "critical";
  known_patterns: string[];
  risk_factors: string[];
  recommendations: string[];
  confidence: number;
  threat_intelligence: {
    malware_association: boolean;
    botnet_link: boolean;
    surveillance_concern: boolean;
  };
}

interface BrainTlsAnalysis {
  normalized_fingerprint: string;
  security_posture: TlsFingerprintAnalysis;
  adaptive_response: "allow" | "warn" | "block" | "investigate";
  learning_opportunity: boolean;
}

class BrainTlsAnalyzer {
  private baseUrl: string;
  private apiKey: string;
  private cache: Map<string, BrainTlsAnalysis>;
  private threatIntelCache: Map<string, any>;

  constructor() {
    this.baseUrl = process.env.IPPOC_BRAIN_URL || "http://localhost:8001";
    this.apiKey = process.env.IPPOC_API_KEY || "";
    this.cache = new Map();
    this.threatIntelCache = new Map();
  }

  normalizeFingerprint(input: string): string {
    const trimmed = input.trim();
    const withoutPrefix = trimmed.replace(/^sha-?256\s*:?\s*/i, "");
    return withoutPrefix.replace(/[^a-fA-F0-9]/g, "").toLowerCase();
  }

  async analyzeTlsFingerprint(fingerprint: string, context?: any): Promise<BrainTlsAnalysis> {
    const normalized = this.normalizeFingerprint(fingerprint);

    // Check cache first
    if (this.cache.has(normalized)) {
      return this.cache.get(normalized)!;
    }

    try {
      // Brain-powered TLS analysis
      const response = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
          "X-Source": "brain-tls-analyzer",
        },
        body: JSON.stringify({
          tool_name: "security",
          domain: "security",
          action: "analyze_tls_fingerprint",
          context: {
            fingerprint: normalized,
            additional_context: context || {},
            threat_intelligence_lookup: true,
            behavioral_analysis: true,
          },
          risk_level: "medium",
          estimated_cost: 0.15,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.output) {
          const analysis: BrainTlsAnalysis = {
            normalized_fingerprint: normalized,
            security_posture: result.output.security_analysis,
            adaptive_response: result.output.recommended_action,
            learning_opportunity: result.output.novel_pattern || false,
          };

          // Cache the result
          this.cache.set(normalized, analysis);

          // Learn from new patterns
          if (analysis.learning_opportunity) {
            this.learnFromNovelFingerprint(analysis);
          }

          return analysis;
        }
      }
    } catch (error) {
      console.warn(`[Brain TLS] Analysis failed for fingerprint ${fingerprint}:`, error);
    }

    // Fallback analysis
    return this.fallbackAnalysis(normalized, context);
  }

  private async fallbackAnalysis(fingerprint: string, context?: any): Promise<BrainTlsAnalysis> {
    // Basic heuristic-based analysis
    const length = fingerprint.length;
    const hasCommonPatterns = this.checkCommonPatterns(fingerprint);
    const entropy = this.calculateEntropy(fingerprint);

    let securityRating: "excellent" | "good" | "fair" | "poor" | "critical" = "fair";
    const riskFactors: string[] = [];
    const recommendations: string[] = [];

    if (length !== 64) {
      riskFactors.push("invalid_length");
      securityRating = "poor";
    }

    if (entropy < 3.5) {
      riskFactors.push("low_entropy");
      recommendations.push("investigate_repeated_patterns");
    }

    if (hasCommonPatterns.knownBad) {
      riskFactors.push("known_malicious_pattern");
      securityRating = "critical";
    } else if (hasCommonPatterns.knownGood) {
      recommendations.push("recognized_secure_client");
      securityRating = "excellent";
    }

    const analysis: TlsFingerprintAnalysis = {
      fingerprint,
      security_rating: securityRating,
      known_patterns: hasCommonPatterns.matches,
      risk_factors: riskFactors,
      recommendations,
      confidence: Math.min(0.8, 0.5 + recommendations.length * 0.1),
      threat_intelligence: {
        malware_association: hasCommonPatterns.knownBad,
        botnet_link: false,
        surveillance_concern: entropy < 2.0,
      },
    };

    const brainAnalysis: BrainTlsAnalysis = {
      normalized_fingerprint: fingerprint,
      security_posture: analysis,
      adaptive_response:
        securityRating === "critical" ? "block" : securityRating === "poor" ? "warn" : "allow",
      learning_opportunity: riskFactors.length === 0 && recommendations.length === 0,
    };

    this.cache.set(fingerprint, brainAnalysis);
    return brainAnalysis;
  }

  private checkCommonPatterns(fingerprint: string): {
    knownGood: boolean;
    knownBad: boolean;
    matches: string[];
  } {
    const patterns = {
      // Known good browser fingerprints (simplified examples)
      good: [
        /^a{64}$/, // Example pattern
        /^b{64}$/, // Example pattern
      ],
      // Known malicious fingerprints
      bad: [
        /^0{64}$/, // Null fingerprint
        /^[0-9a-f]{32}0{32}$/, // Suspicious padding
      ],
    };

    const matches: string[] = [];
    let knownGood = false;
    let knownBad = false;

    for (const pattern of patterns.good) {
      if (pattern.test(fingerprint)) {
        matches.push("known_good_pattern");
        knownGood = true;
      }
    }

    for (const pattern of patterns.bad) {
      if (pattern.test(fingerprint)) {
        matches.push("known_malicious_pattern");
        knownBad = true;
      }
    }

    return { knownGood, knownBad, matches };
  }

  private calculateEntropy(hexString: string): number {
    if (hexString.length === 0) return 0;

    const frequencies: Record<string, number> = {};
    for (const char of hexString) {
      frequencies[char] = (frequencies[char] || 0) + 1;
    }

    let entropy = 0;
    const len = hexString.length;

    for (const freq of Object.values(frequencies)) {
      const probability = freq / len;
      entropy -= probability * Math.log2(probability);
    }

    return entropy;
  }

  private async learnFromNovelFingerprint(analysis: BrainTlsAnalysis): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/v1/tools/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
          "X-Source": "brain-tls-analyzer",
        },
        body: JSON.stringify({
          tool_name: "evolution",
          domain: "evolution",
          action: "learn_novel_tls_pattern",
          context: {
            fingerprint: analysis.normalized_fingerprint,
            security_posture: analysis.security_posture,
            context_features: {
              entropy: this.calculateEntropy(analysis.normalized_fingerprint),
              length: analysis.normalized_fingerprint.length,
            },
          },
          risk_level: "low",
          estimated_cost: 0.1,
        }),
      });
    } catch (error) {
      console.warn("[Brain TLS] Failed to learn from novel fingerprint:", error);
    }
  }

  async getThreatIntelligence(fingerprint: string): Promise<any> {
    const normalized = this.normalizeFingerprint(fingerprint);

    if (this.threatIntelCache.has(normalized)) {
      return this.threatIntelCache.get(normalized);
    }

    try {
      const response = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
          "X-Source": "brain-tls-threat-intel",
        },
        body: JSON.stringify({
          tool_name: "security",
          domain: "security",
          action: "lookup_threat_intelligence",
          context: {
            fingerprint: normalized,
            lookup_type: "tls_fingerprint",
          },
          risk_level: "medium",
          estimated_cost: 0.2,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          this.threatIntelCache.set(normalized, result.output);
          return result.output;
        }
      }
    } catch (error) {
      console.warn(`[Brain TLS] Threat intel lookup failed for ${fingerprint}:`, error);
    }

    return null;
  }

  // Public API methods
  async shouldAllowConnection(fingerprint: string, context?: any): Promise<boolean> {
    const analysis = await this.analyzeTlsFingerprint(fingerprint, context);
    return analysis.adaptive_response !== "block";
  }

  async getConnectionRisk(
    fingerprint: string,
    context?: any,
  ): Promise<{
    risk_level: "low" | "medium" | "high" | "critical";
    reasons: string[];
    recommendations: string[];
  }> {
    const analysis = await this.analyzeTlsFingerprint(fingerprint, context);

    return {
      risk_level:
        analysis.security_posture.security_rating === "excellent"
          ? "low"
          : analysis.security_posture.security_rating === "good"
            ? "low"
            : analysis.security_posture.security_rating === "fair"
              ? "medium"
              : analysis.security_posture.security_rating === "poor"
                ? "high"
                : "critical",
      reasons: analysis.security_posture.risk_factors,
      recommendations: analysis.security_posture.recommendations,
    };
  }

  async logSuspiciousFingerprint(fingerprint: string, context?: any): Promise<void> {
    const analysis = await this.analyzeTlsFingerprint(fingerprint, context);

    if (
      analysis.adaptive_response === "investigate" ||
      analysis.security_posture.security_rating === "critical"
    ) {
      console.warn(`[Brain TLS] Suspicious fingerprint detected:`, {
        fingerprint: analysis.normalized_fingerprint,
        security_rating: analysis.security_posture.security_rating,
        risk_factors: analysis.security_posture.risk_factors,
        confidence: analysis.security_posture.confidence,
      });

      // In a real system, this would trigger alerts or logging
    }
  }

  getCacheStats(): { totalEntries: number; hitRate: number } {
    // Simplified cache stats - in reality would track hits/misses
    return {
      totalEntries: this.cache.size,
      hitRate: 0.85, // Placeholder
    };
  }

  clearCache(): void {
    this.cache.clear();
    this.threatIntelCache.clear();
  }
}

// Export singleton instance
export const brainTlsAnalyzer = new BrainTlsAnalyzer();

// Backward compatibility exports
export function normalizeFingerprint(input: string): string {
  return brainTlsAnalyzer.normalizeFingerprint(input);
}

export async function analyzeTlsSecurity(
  fingerprint: string,
  context?: any,
): Promise<BrainTlsAnalysis> {
  return brainTlsAnalyzer.analyzeTlsFingerprint(fingerprint, context);
}

export async function isTlsConnectionSafe(fingerprint: string, context?: any): Promise<boolean> {
  return brainTlsAnalyzer.shouldAllowConnection(fingerprint, context);
}
