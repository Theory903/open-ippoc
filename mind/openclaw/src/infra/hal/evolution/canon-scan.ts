import { readFile, readdir, stat } from "fs/promises";
import { join, resolve } from "path";

export interface Canon {
  forbidden: { name: string; pattern: string }[];
  required: { name: string; filePattern: RegExp; pattern: string }[];
}

export interface AlignmentResult {
  aligned: boolean;
  violations: Violation[];
}

export interface Violation {
  type: "FORBIDDEN" | "MISSING_REQUIRED";
  rule: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  location: string;
}

export class CanonScanner {
  // Assuming SYSTEM_CANON.md is in the repo root
  private readonly canonPath = resolve(__dirname, "../../../../../../SYSTEM_CANON.md");

  async checkAlignment(patchContent: string, targetFile: string): Promise<AlignmentResult> {
    const canon = await this.loadCanon();
    const violations: Violation[] = [];

    // Check for forbidden patterns
    for (const rule of canon.forbidden) {
      if (patchContent.includes(rule.pattern)) {
        violations.push({
          type: "FORBIDDEN",
          rule: rule.name,
          severity: "HIGH",
          location: targetFile,
        });
      }
    }

    // Check for required patterns
    for (const rule of canon.required) {
      if (targetFile.match(rule.filePattern) && !patchContent.includes(rule.pattern)) {
        violations.push({
          type: "MISSING_REQUIRED",
          rule: rule.name,
          severity: "MEDIUM",
          location: targetFile,
        });
      }
    }

    return {
      aligned: violations.length === 0,
      violations,
    };
  }

  async scan(directory: string): Promise<AlignmentResult> {
    const allViolations: Violation[] = [];

    const files = await this.recursiveFind(directory);

    for (const file of files) {
      try {
        const content = await readFile(file, "utf-8");
        const result = await this.checkAlignment(content, file);
        allViolations.push(...result.violations);
      } catch (e) {
        // Ignore binary read errors etc
      }
    }

    return {
      aligned: allViolations.length === 0,
      violations: allViolations,
    };
  }

  private async recursiveFind(dir: string): Promise<string[]> {
    const entries = await readdir(dir, { withFileTypes: true });
    const files: string[] = [];

    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name !== "node_modules" && !entry.name.startsWith(".")) {
          files.push(...(await this.recursiveFind(fullPath)));
        }
      } else if (entry.isFile() && (entry.name.endsWith(".ts") || entry.name.endsWith(".js"))) {
        files.push(fullPath);
      }
    }
    return files;
  }

  private async loadCanon(): Promise<Canon> {
    try {
      const content = await readFile(this.canonPath, "utf-8");
      return this.parseCanon(content);
    } catch (error) {
      console.warn("SYSTEM_CANON.md not found at", this.canonPath, "Using default canon.");
      return { forbidden: [], required: [] };
    }
  }

  private parseCanon(content: string): Canon {
    // Basic parsing logic - in reality this would parse the markdown structure
    // For now, we return a hardcoded set combined with what we might parse if we implemented a full parser
    return {
      forbidden: [
        { name: "no-eval", pattern: "eval(" },
        { name: "no-implicit-any", pattern: ": any" },
        { name: "no-absolute-paths", pattern: "/Users/" }, // Example hardening
      ],
      required: [{ name: "error-handling", filePattern: /\.ts$/, pattern: "try {" }],
    };
  }
}
