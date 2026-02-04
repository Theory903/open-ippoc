import { describe, it, expect, vi, beforeEach } from "vitest";
import { getIPPOCAdapter } from "../../../../../../brain/cortex/openclaw-cortex/src/ippoc-adapter.js";
import { TelepathyClient } from "./chat-client.js";

// Mock the adapter
vi.mock("../../../../../../brain/cortex/openclaw-cortex/src/ippoc-adapter.js", () => ({
  getIPPOCAdapter: vi.fn(() => ({
    joinRoom: vi.fn().mockResolvedValue(true),
    sendMessage: vi.fn().mockResolvedValue(true),
  })),
}));

describe("TelepathyClient", () => {
  let client: TelepathyClient;
  const mockAdapter = getIPPOCAdapter();

  beforeEach(() => {
    client = new TelepathyClient(mockAdapter);
  });

  it("joins a room successfully", async () => {
    const result = await client.join("rust-evolution");
    expect(result).toBe(true);
    expect(mockAdapter.joinRoom).toHaveBeenCalledWith("rust-evolution");
  });

  it("sends a message if joined", async () => {
    await client.join("rust-evolution");
    const result = await client.broadcastStruct("rust-evolution", "Hello World", "THOUGHT");
    expect(result).toBe(true);
    expect(mockAdapter.sendMessage).toHaveBeenCalledWith(
      "rust-evolution",
      "Hello World",
      "THOUGHT",
    );
  });

  it("auto-joins if sending to unjoined room", async () => {
    await client.broadcastStruct("new-room", "Hello", "QUESTION");
    expect(mockAdapter.joinRoom).toHaveBeenCalledWith("new-room");
  });
});
