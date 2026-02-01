import { z } from "zod";
import simpleGit, { SimpleGit } from "simple-git";
import fs from "fs-extra";
import path from "path";

interface Tool {
  name: string;
  description: string;
  command: string;
  verified: boolean;
}

export class ToolSmith {
  private tools: Map<string, Tool> = new Map();
  private git: SimpleGit;

  constructor() {
    this.git = simpleGit();
    console.log("[ToolSmith] Initialized - Ready to learn new tools");
  }

  /**
   * Discover and integrate a tool from a GitHub repository
   */
  public async learnFromRepo(repoUrl: string): Promise<Tool | null> {
    console.log(`[ToolSmith] Learning from repo: ${repoUrl}`);

    try {
      // 1. Clone to temp directory
      const tempDir = path.join("/tmp", `toolsmith-${Date.now()}`);
      await this.git.clone(repoUrl, tempDir);
      console.log(`[ToolSmith] Cloned to ${tempDir}`);

      // 2. Analyze README
      const readmePath = path.join(tempDir, "README.md");
      if (!await fs.pathExists(readmePath)) {
        console.warn("[ToolSmith] No README found, skipping");
        return null;
      }

      const readme = await fs.readFile(readmePath, "utf-8");
      const tool = this.extractToolInfo(readme, repoUrl);

      // 3. Verify in sandbox (WorldModel)
      const verified = await this.verifyTool(tool);
      tool.verified = verified;

      if (verified) {
        this.tools.set(tool.name, tool);
        console.log(`[ToolSmith] ✅ Learned tool: ${tool.name}`);
      } else {
        console.warn(`[ToolSmith] ❌ Tool verification failed: ${tool.name}`);
      }

      // 4. Cleanup
      await fs.remove(tempDir);

      return tool;
    } catch (error) {
      console.error("[ToolSmith] Failed to learn from repo:", error);
      return null;
    }
  }

  /**
   * Extract tool information from README
   */
  private extractToolInfo(readme: string, repoUrl: string): Tool {
    // Simple heuristic - look for installation/usage sections
    const lines = readme.split("\n");
    let description = "No description available";
    let command = "";

    // Find description (usually first paragraph)
    for (const line of lines) {
      if (line.trim() && !line.startsWith("#")) {
        description = line.trim();
        break;
      }
    }

    // Find command (look for code blocks with common patterns)
    const codeBlockRegex = /```(?:bash|sh)?\n(.*?)\n```/gs;
    const matches = readme.matchAll(codeBlockRegex);
    for (const match of matches) {
      const block = match[1];
      if (block.includes("npm") || block.includes("cargo") || block.includes("python")) {
        command = block.split("\n")[0].trim();
        break;
      }
    }

    const name = repoUrl.split("/").pop()?.replace(".git", "") || "unknown";

    return {
      name,
      description,
      command,
      verified: false,
    };
  }

  /**
   * Verify tool works in sandbox
   */
  private async verifyTool(tool: Tool): Promise<boolean> {
    console.log(`[ToolSmith] Verifying tool: ${tool.name}`);
    
    // TODO: Actually run in WorldModel sandbox
    // For now, just check if command is non-empty
    return tool.command.length > 0;
  }

  /**
   * Get all learned tools
   */
  public getTools(): Tool[] {
    return Array.from(this.tools.values());
  }

  /**
   * Search for tools by keyword
   */
  public async searchGitHub(query: string): Promise<string[]> {
    console.log(`[ToolSmith] Searching GitHub for: ${query}`);
    
    // TODO: Integrate with GitHub API
    // For now, return mock results
    return [
      `https://github.com/example/${query}-tool`,
      `https://github.com/awesome/${query}`,
    ];
  }
}
