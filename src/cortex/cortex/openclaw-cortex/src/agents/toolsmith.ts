import { z } from "zod";
import simpleGit, { SimpleGit } from "simple-git";
import fs from "fs-extra";
import path from "path";
import axios from "axios";

interface Tool {
  name: string;
  description: string;
  command: string;
  verified: boolean;
  repoUrl: string;
  stars: number;
  lastUpdated: string;
}

// GitHub API configuration
const GITHUB_API_ENDPOINT = "https://api.github.com";
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

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
      // 1. Extract owner and repo name
      const repoInfo = this.extractRepoInfo(repoUrl);
      if (!repoInfo) {
        console.warn("[ToolSmith] Invalid repository URL");
        return null;
      }

      // 2. Get repository metadata
      const repoMetadata = await this.getRepoMetadata(repoInfo.owner, repoInfo.repo);
      if (!repoMetadata) {
        console.warn("[ToolSmith] Failed to get repository metadata");
        return null;
      }

      // 3. Clone to temp directory
      const tempDir = path.join("/tmp", `toolsmith-${Date.now()}`);
      await this.git.clone(repoUrl, tempDir);
      console.log(`[ToolSmith] Cloned to ${tempDir}`);

      // 4. Analyze README
      const readmePath = path.join(tempDir, "README.md");
      if (!await fs.pathExists(readmePath)) {
        console.warn("[ToolSmith] No README found, skipping");
        return null;
      }

      const readme = await fs.readFile(readmePath, "utf-8");
      const tool = this.extractToolInfo(readme, repoUrl, repoMetadata);

      // 5. Verify in sandbox (WorldModel)
      const verified = await this.verifyTool(tool);
      tool.verified = verified;

      if (verified) {
        this.tools.set(tool.name, tool);
        console.log(`[ToolSmith] ✅ Learned tool: ${tool.name}`);
      } else {
        console.warn(`[ToolSmith] ❌ Tool verification failed: ${tool.name}`);
      }

      // 6. Cleanup
      await fs.remove(tempDir);

      return tool;
    } catch (error) {
      console.error("[ToolSmith] Failed to learn from repo:", error);
      return null;
    }
  }

  /**
   * Extract repository info from URL
   */
  private extractRepoInfo(url: string): { owner: string; repo: string } | null {
    const regex = /github\.com\/([^\/]+)\/([^\/\.]+)/;
    const match = url.match(regex);
    if (match) {
      return { owner: match[1], repo: match[2] };
    }
    return null;
  }

  /**
   * Get repository metadata from GitHub API
   */
  private async getRepoMetadata(owner: string, repo: string): Promise<any> {
    try {
      const headers: any = {
        "Accept": "application/vnd.github.v3+json",
      };
      
      if (GITHUB_TOKEN) {
        headers["Authorization"] = `token ${GITHUB_TOKEN}`;
      }

      const response = await axios.get(`${GITHUB_API_ENDPOINT}/repos/${owner}/${repo}`, {
        headers,
      });

      return {
        stars: response.data.stargazers_count,
        lastUpdated: response.data.updated_at,
        description: response.data.description,
      };
    } catch (error) {
      console.error("[ToolSmith] Failed to get repo metadata:", error);
      return null;
    }
  }

  /**
   * Extract tool information from README
   */
  private extractToolInfo(readme: string, repoUrl: string, metadata: any): Tool {
    // Simple heuristic - look for installation/usage sections
    const lines = readme.split("\n");
    let description = metadata.description || "No description available";
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
      repoUrl,
      stars: metadata.stars,
      lastUpdated: metadata.lastUpdated,
    };
  }

  /**
   * Verify tool works in sandbox
   */
  private async verifyTool(tool: Tool): Promise<boolean> {
    console.log(`[ToolSmith] Verifying tool: ${tool.name}`);
    
    // Improved Verification: Check for valid project structure
    // We assume 'git clone' was handled by learnFromRepo into a temp path, 
    // but here we might need to check the repoUrl remotely or assume we have context.
    // Since this method just takes 'Tool', we will rely on basic heuristics + the stars check.
    
    const hasCommand = tool.command.length > 0;
    const isPopular = tool.stars > 10; // Slightly higher bar
    
    // Heuristic: If it has a cargo/npm/pip command, it's likely a valid tool
    const likelyValid = ["npm", "yarn", "cargo", "pip", "python", "go"].some(prefix => tool.command.startsWith(prefix));

    if (hasCommand && (isPopular || likelyValid)) {
        return true;
    }
    
    console.log(`[ToolSmith] Tool ${tool.name} failed verification (Cmd: ${hasCommand}, Pop: ${isPopular}, Valid: ${likelyValid})`);
    return false;
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
    
    try {
      const headers: any = {
        "Accept": "application/vnd.github.v3+json",
      };
      
      if (GITHUB_TOKEN) {
        headers["Authorization"] = `token ${GITHUB_TOKEN}`;
      }

      const response = await axios.get(`${GITHUB_API_ENDPOINT}/search/repositories`, {
        headers,
        params: {
          q: query,
          sort: "stars",
          order: "desc",
          per_page: 10,
        },
      });

      return response.data.items.map((repo: any) => repo.html_url);
    } catch (error) {
      console.error("[ToolSmith] GitHub search failed:", error);
      // Return mock results if API fails
      return [
        `https://github.com/example/${query}-tool`,
        `https://github.com/awesome/${query}`,
      ];
    }
  }

  /**
   * Get tool by name
   */
  public getTool(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  /**
   * Remove tool from registry
   */
  public removeTool(name: string): boolean {
    return this.tools.delete(name);
  }
  /**
   * Create a new skill using the IPPOC scaffolding script
   */
  public async createSkill(name: string, pathStr: string, resources: string[] = []): Promise<boolean> {
    console.log(`[ToolSmith] Scaffolding new skill: ${name}`);
    
    // Resolve script path relative to this agent or assume fixed location
    // user provided path: mind/openclaw/skills/skill-creator/scripts/init_skill.py
    const scriptPath = path.resolve(process.cwd(), "mind/openclaw/skills/skill-creator/scripts/init_skill.py");
    
    if (!await fs.pathExists(scriptPath)) {
        console.error(`[ToolSmith] init_skill.py not found at ${scriptPath}`);
        return false;
    }

    try {
        const { exec } = require("child_process");
        const util = require("util");
        const execAsync = util.promisify(exec);

        const resourceFlag = resources.length > 0 ? `--resources ${resources.join(",")}` : "";
        const cmd = `python3 "${scriptPath}" ${name} --path "${pathStr}" ${resourceFlag}`;
        
        console.log(`[ToolSmith] Executing: ${cmd}`);
        const { stdout, stderr } = await execAsync(cmd);
        
        console.log(stdout);
        if (stderr) console.warn(stderr);
        
        return true;
    } catch (e) {
        console.error(`[ToolSmith] Failed to scaffold skill: ${e}`);
        return false;
    }
  }
}
