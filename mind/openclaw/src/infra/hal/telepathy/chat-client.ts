import { getIPPOCAdapter } from "../../../../../../brain/cortex/openclaw-cortex/src/ippoc-adapter.js";

export class TelepathyClient {
  private rooms: Set<string> = new Set();

  constructor(private adapter = getIPPOCAdapter()) {}

  /**
   * Join a chat room (e.g., 'rust-evolution', 'economy')
   */
  async join(roomId: string): Promise<boolean> {
    const success = await this.adapter.joinRoom(roomId);
    if (success) {
      this.rooms.add(roomId);
      console.log(`[HAL:Telepathy] Joined room: ${roomId}`);
    } else {
      console.warn(`[HAL:Telepathy] Failed to join room: ${roomId}`);
    }
    return success;
  }

  /**
   * Broadcast a thought to a room
   */
  async broadcastStruct(
    roomId: string,
    content: string,
    type: "THOUGHT" | "QUESTION" | "REVIEW" = "THOUGHT",
  ): Promise<boolean> {
    if (!this.rooms.has(roomId)) {
      console.warn(`[HAL:Telepathy] Not member of room: ${roomId}. Attempting auto-join...`);
      await this.join(roomId);
    }

    return this.adapter.sendMessage(roomId, content, type);
  }

  /**
   * Leave a room
   */
  async leave(roomId: string): Promise<void> {
    this.rooms.delete(roomId);
    // Currently adapter doesn't support explicit leave, just local track.
    console.log(`[HAL:Telepathy] Left room (local): ${roomId}`);
  }
}
