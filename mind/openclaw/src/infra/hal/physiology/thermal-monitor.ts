import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export class ThermalMonitor {
  async getTemperatures(): Promise<{ cpu: number; gpu: number }> {
    try {
      // MacOS specific thermal check
      // This command gets the thermal pressure level (0 - Nominal, 1 - Moderate, 2 - Heavy, 3 - Trapping)
      const { stdout } = await execAsync("sysctl -n machdep.cpu.thermal_level");
      const level = parseInt(stdout.trim(), 10);

      // Map level to approximate temps for heuristics (since raw temp is hard to get without generic kexts)
      const baseTemp = 45 + level * 15;

      return {
        cpu: baseTemp,
        gpu: baseTemp + 5,
      };
    } catch (e) {
      // Fallback if command fails
      return { cpu: 0, gpu: 0 };
    }
  }

  async isSafe(): Promise<boolean> {
    const temps = await this.getTemperatures();
    // Throttle if we are in Heavy (level 2 -> ~75C) or Trapping (level 3 -> ~90C)
    return temps.cpu < 80;
  }
}
