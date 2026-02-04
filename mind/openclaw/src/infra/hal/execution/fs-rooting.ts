import { mkdir, access } from "fs/promises";
import { join } from "path";

export class NodeRootManager {
  private readonly baseDir = "/var/ippoc/nodes";

  async createNodeRoot(nodeId: string): Promise<string> {
    const nodeRoot = join(this.baseDir, nodeId);

    await mkdir(join(nodeRoot, "sandbox"), { recursive: true });
    await mkdir(join(nodeRoot, "memory"), { recursive: true });
    await mkdir(join(nodeRoot, "logs"), { recursive: true });
    await mkdir(join(nodeRoot, "models"), { recursive: true });

    return nodeRoot;
  }

  getNodePath(nodeId: string, subdir: "sandbox" | "memory" | "logs" | "models"): string {
    return join(this.baseDir, nodeId, subdir);
  }

  async validatePath(nodeId: string, requestedPath: string): Promise<boolean> {
    const nodeRoot = join(this.baseDir, nodeId);
    try {
      await access(nodeRoot);
      return requestedPath.startsWith(nodeRoot);
    } catch {
      return false;
    }
  }
}
