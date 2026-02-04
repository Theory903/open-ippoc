import { mkdir, access } from "fs/promises";
import { join } from "path";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { NodeRootManager } from "./fs-rooting";

// Mock fs/promises
vi.mock("fs/promises", () => ({
  mkdir: vi.fn(),
  access: vi.fn(),
}));

describe("NodeRootManager", () => {
  let manager: NodeRootManager;

  beforeEach(() => {
    manager = new NodeRootManager();
    vi.clearAllMocks();
  });

  it("should generate correct paths", () => {
    const path = manager.getNodePath("node-123", "sandbox");
    expect(path).toBe("/var/ippoc/nodes/node-123/sandbox");
  });

  it("should create node root directories", async () => {
    await manager.createNodeRoot("node-abc");
    expect(mkdir).toHaveBeenCalledTimes(4); // sandbox, memory, logs, models
    expect(mkdir).toHaveBeenCalledWith("/var/ippoc/nodes/node-abc/sandbox", { recursive: true });
  });

  it("should validate paths inside sandbox", async () => {
    vi.mocked(access).mockResolvedValue(undefined); // path exists

    const isValid = await manager.validatePath(
      "node-123",
      "/var/ippoc/nodes/node-123/sandbox/script.js",
    );
    expect(isValid).toBe(true);
  });

  it("should reject paths outside sandbox (traversal attempt)", async () => {
    vi.mocked(access).mockResolvedValue(undefined);

    const isValid = await manager.validatePath("node-123", "/etc/passwd");
    expect(isValid).toBe(false);
  });

  it("should handle non-existent roots gracefully", async () => {
    vi.mocked(access).mockRejectedValue(new Error("ENOENT"));

    const isValid = await manager.validatePath(
      "node-ghost",
      "/var/ippoc/nodes/node-ghost/file.txt",
    );
    expect(isValid).toBe(false);
  });
});
