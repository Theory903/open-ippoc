import * as fs from "fs/promises";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OpportunityDetector } from "./opportunity-detector.js";
import { StrategicRefactor } from "./strategic-refactor.js";
import { VisionMemory } from "./vision-memory.js";

vi.mock("fs/promises");

describe("Cognition Layer", () => {
  describe("OpportunityDetector", () => {
    it("should detect patterns after threshold", async () => {
      const detector = new OpportunityDetector();
      // Mock notifyBrain
      const spy = vi.spyOn(detector as any, "notifyBrain").mockResolvedValue(undefined);

      detector.recordFailure("task1", "timeout error");
      detector.recordFailure("task2", "timeout error");
      detector.recordFailure("task3", "timeout error");

      expect(spy).toHaveBeenCalledTimes(1);
      expect(spy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "MISSING_CAPABILITY",
          description: expect.stringContaining("timeout-prone-tasks"),
        }),
      );
    });
  });

  describe("StrategicRefactor", () => {
    it("should propose refactors for expensive paths", async () => {
      const refactor = new StrategicRefactor();

      // Simulate 11 runs (threshold 10) with high complexity (threshold 50)
      for (let i = 0; i < 11; i++) {
        refactor.recordPathCost("heavy/path", 1000, 60);
      }

      const proposals = await refactor.analyzeRefactorOpportunities();
      expect(proposals).toHaveLength(1);
      expect(proposals[0].path).toBe("heavy/path");
      expect(proposals[0].estimatedSavings).toBeGreaterThan(0);
    });

    it("should ignore cheap paths", async () => {
      const refactor = new StrategicRefactor();

      for (let i = 0; i < 11; i++) {
        refactor.recordPathCost("easy/path", 10, 10);
      }

      const proposals = await refactor.analyzeRefactorOpportunities();
      expect(proposals).toHaveLength(0);
    });
  });

  describe("VisionMemory", () => {
    let memory: VisionMemory;

    beforeEach(() => {
      memory = new VisionMemory();
      vi.mocked(fs.readFile).mockResolvedValue("[]");
      vi.mocked(fs.writeFile).mockResolvedValue(undefined);
    });

    it("should add goals and save", async () => {
      await memory.addGoal({
        description: "World Domination",
        createdAt: Date.now(),
        timelineMs: 100000,
        milestones: [],
      });

      expect(fs.writeFile).toHaveBeenCalled();
    });

    it("should evaluate progress", async () => {
      await memory.loadVision(); // loads empty
      const report = await memory.evaluateProgress();
      expect(report.goals).toHaveLength(0);
    });
  });
});
