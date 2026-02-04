import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { OrganHealth } from "./organ-health.js";
import { PainAggregator, PainLevel } from "./pain-aggregator.js";
import { SidecarOrchestrator } from "./sidecar-orchestrator.js";

vi.mock("child_process", () => {
  return {
    spawn: vi.fn(() => ({
      pid: 123,
      killed: false,
      exitCode: null,
      on: vi.fn(),
      kill: vi.fn(),
    })),
  };
});

describe("Physiology Layer", () => {
  describe("PainAggregator", () => {
    let aggregator: PainAggregator;

    beforeEach(() => {
      aggregator = new PainAggregator();
    });

    it("should aggregate pain levels correctly", () => {
      aggregator.report("modA", PainLevel.LOW, "minor glitch");
      expect(aggregator.getAggregate().level).toBe(PainLevel.LOW);

      aggregator.report("modB", PainLevel.HIGH, "major fail");
      expect(aggregator.getAggregate().level).toBe(PainLevel.MEDIUM); // 1 HIGH -> MEDIUM

      aggregator.report("modC", PainLevel.HIGH, "major fail 2");
      aggregator.report("modD", PainLevel.HIGH, "major fail 3");
      expect(aggregator.getAggregate().level).toBe(PainLevel.HIGH); // > 2 HIGH -> HIGH
    });

    it("should trigger critical on single critical signal", () => {
      aggregator.report("modA", PainLevel.CRITICAL, "system panick");
      expect(aggregator.getAggregate().level).toBe(PainLevel.CRITICAL);
    });
  });

  describe("SidecarOrchestrator", () => {
    let orchestrator: SidecarOrchestrator;

    beforeEach(() => {
      orchestrator = new SidecarOrchestrator();
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
      orchestrator.stopAll();
    });

    it("should start a sidecar", async () => {
      await orchestrator.startSidecar("test-model", "/path/to/model", { modelPath: "", env: {} });
      // Cannot easily access private map without reflecting or adding getter.
      // verifying no throw is basic check.
    });

    // Complex behavioral tests for restart require more detailed mocking of ChildProcess events
  });

  describe("OrganHealth", () => {
    it("should report ALIVE for running process", () => {
      const health = new OrganHealth();
      const proc = { killed: false, exitCode: null };
      expect(health.check({ process: proc })).toEqual({ status: "ALIVE" });
    });

    it("should report DEAD for killed process", () => {
      const health = new OrganHealth();
      const proc = { killed: true, exitCode: null };
      expect(health.check({ process: proc })).toEqual({ status: "DEAD", reason: "Process exited" });
    });
  });
});
