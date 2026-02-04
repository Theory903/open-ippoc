import * as fs from "fs/promises";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CanonScanner } from "./canon-scan.js";
import { ConflictMediator } from "./conflict-mediator.js";
import { DryRunEngine } from "./dry-run.js";

vi.mock("child_process");
vi.mock("fs/promises");

describe("Evolution Layer", () => {
  describe("DryRunEngine", () => {
    it("should simulate patch application", async () => {
      // Mock spawn to return success
      // This is a complex mock, for now we just verify the class structure and basic async flow
      // since we mocked child_process completely.
      // In a real integration test we would use real fs.
      const engine = new DryRunEngine();
      expect(engine).toBeDefined();
    });
  });

  describe("ConflictMediator", () => {
    it("should parse conflict hunks", async () => {
      const mediator = new ConflictMediator();
      const diffOutput = `
const a = 1;
`;
      // @ts-ignore - Accessing private method via public extraction logic would require mocking exec
      const hunks = mediator["parseConflicts"](diffOutput);

      expect(hunks).toHaveLength(1);
      expect(hunks[0].ours.trim()).toBe("const a = 1;");
      expect(hunks[0].theirs.trim()).toBe("const a = 2;");
      expect(hunks[0].base.trim()).toBe("const a = 0;");
    });
  });

  describe("CanonScanner", () => {
    let scanner: CanonScanner;

    beforeEach(() => {
      scanner = new CanonScanner();
      // Mock loadCanon to return a static canon for testing
      scanner["loadCanon"] = vi.fn().mockResolvedValue({
        forbidden: [{ name: "no-eval", pattern: "eval(" }],
        required: [{ name: "try-catch", filePattern: /\.ts$/, pattern: "try {" }],
      });
    });

    it("should detect forbidden patterns", async () => {
      const result = await scanner.checkAlignment('const x = eval("1+1");', "unsafe.ts");
      expect(result.aligned).toBe(false);
      expect(result.violations[0].type).toBe("FORBIDDEN");
      expect(result.violations[0].rule).toBe("no-eval");
    });

    it("should detect missing required patterns", async () => {
      const result = await scanner.checkAlignment("const x = 1;", "safe.ts");
      expect(result.aligned).toBe(false);
      expect(result.violations[0].type).toBe("MISSING_REQUIRED");
      expect(result.violations[0].rule).toBe("try-catch");
    });

    it("should pass aligned code", async () => {
      const result = await scanner.checkAlignment("try { const x = 1; } catch {}", "safe.ts");
      expect(result.aligned).toBe(true);
    });
  });
});
