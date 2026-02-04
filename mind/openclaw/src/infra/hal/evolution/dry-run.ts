import { spawn } from "child_process";
import { mkdir, copyFile, writeFile } from "fs/promises";
import { join } from "path";

export interface DryRunResult {
  success: boolean;
  output: string;
}

export class DryRunEngine {
  async simulate(patchContent: string, targetFile: string): Promise<DryRunResult> {
    const tempDir = join("/tmp", "ippoc-dryrun", Date.now().toString());
    await mkdir(tempDir, { recursive: true });

    // Copy target file to temp
    const tempFile = join(tempDir, "target.ts");
    await copyFile(targetFile, tempFile);

    // Apply patch in temp
    const patchFile = join(tempDir, "patch.diff");
    await writeFile(patchFile, patchContent);

    const result = await this.applyPatch(tempFile, patchFile);

    if (result.success) {
      // Run tests in temp directory
      const testResult = await this.runTests(tempDir);
      return { success: testResult.success, output: testResult.output };
    }

    return { success: false, output: result.output };
  }

  private async applyPatch(
    file: string,
    patch: string,
  ): Promise<{ success: boolean; output: string }> {
    return new Promise((resolve) => {
      const proc = spawn("patch", [file, patch]);
      let output = "";

      proc.stdout.on("data", (data) => (output += data.toString()));
      proc.stderr.on("data", (data) => (output += data.toString()));

      proc.on("close", (code) => {
        resolve({ success: code === 0, output });
      });
    });
  }

  private async runTests(dir: string): Promise<{ success: boolean; output: string }> {
    return new Promise((resolve) => {
      const proc = spawn("npm", ["test"], { cwd: dir });
      let output = "";

      proc.stdout.on("data", (data) => (output += data.toString()));
      proc.stderr.on("data", (data) => (output += data.toString()));

      proc.on("close", (code) => {
        resolve({ success: code === 0, output });
      });
    });
  }
}
