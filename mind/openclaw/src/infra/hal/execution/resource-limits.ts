export interface ResourceUsage {
  cpu: number;
  memory: number;
  gpu: number;
}

export class ResourceLimits {
  private limits: ResourceUsage = {
    cpu: 80, // 80%
    memory: 4096, // 4GB
    gpu: 90, // 90%
  };

  check(usage: ResourceUsage): boolean {
    if (usage.cpu > this.limits.cpu) return false;
    if (usage.memory > this.limits.memory) return false;
    if (usage.gpu > this.limits.gpu) return false;
    return true;
  }

  getLimits(): ResourceUsage {
    return { ...this.limits };
  }
}
