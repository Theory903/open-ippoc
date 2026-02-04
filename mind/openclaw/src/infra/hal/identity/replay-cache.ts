export class ReplayCache {
  private cache = new Map<string, number>();
  private readonly TTL_MS = 5 * 60 * 1000; // 5 minutes

  /**
   * Checks if a nonce has been seen before.
   * If seen and not expired, returns true.
   * If seen but expired, returns false (and cleans up).
   * If not seen, returns false.
   */
  seen(nonce: string): boolean {
    const timestamp = this.cache.get(nonce);
    if (!timestamp) return false;

    if (Date.now() - timestamp > this.TTL_MS) {
      this.cache.delete(nonce);
      return false;
    }

    return true;
  }

  /**
   * Marks a nonce as seen.
   */
  mark(nonce: string): void {
    this.cache.set(nonce, Date.now());
    this.cleanup();
  }

  /**
   * Cleans up expired nonces to prevent memory leaks.
   */
  private cleanup(): void {
    const now = Date.now();
    // Optimization: Only cleanup if map gets too large?
    // For now, simple iteration is fine for typical handshake volumes.
    if (this.cache.size > 10000) {
      for (const [nonce, timestamp] of Array.from(this.cache.entries())) {
        if (now - timestamp > this.TTL_MS) {
          this.cache.delete(nonce);
        }
      }
    }
  }
}
