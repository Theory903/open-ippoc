import { CanonScanner } from "./canon-scan.js";

export class GovernanceValidator {
  constructor(private canon: CanonScanner) {}

  async validateProposal(proposalId: string, diff: string): Promise<boolean> {
    console.log(`[Governance] Validating proposal ${proposalId}...`);

    // 1. Check against Canon (The Code Constitution)
    const alignment = await this.canon.checkAlignment(diff, "patch.diff");
    if (!alignment.aligned) {
      console.warn(`[Governance] ❌ Proposal ${proposalId} violates Canon:`, alignment.violations);
      return false;
    }

    // 2. Sanity Check: Does it touch critical paths?
    if (diff.includes("src/infra/hal/identity") && !diff.includes("HAL_SIGNED")) {
      console.warn(`[Governance] ❌ Critical path modification without signature.`);
      return false;
    }

    // 3. Size check (Rule 6: Modification Scope)
    const lines = diff.split("\n").length;
    if (lines > 300) {
      console.warn(`[Governance] ❌ Change too large (${lines} lines). Rule 6 Violation.`);
      return false;
    }

    console.log(`[Governance] ✅ Proposal ${proposalId} passed checks.`);
    return true;
  }
}
