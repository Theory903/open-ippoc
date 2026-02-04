// mind/openclaw/src/infra/hal/collective/swarm-coordinator.ts
// @collective - Multi-node coordination and swarm intelligence

import { randomBytes } from "crypto";
import { EventEmitter } from "events";

function generateNodeId(): string {
  return randomBytes(16).toString("hex");
}

export interface NodeHandle {
  nodeId: string;
  address: string;
  capabilities: string[];
  status: "active" | "inactive" | "degraded";
  lastSeen: number;
  performanceMetrics: PerformanceMetrics;
}

export interface PerformanceMetrics {
  cpuUsage: number;
  memoryUsage: number;
  networkLatency: number;
  taskCompletionRate: number;
  errorRate: number;
}

export interface Task {
  taskId: string;
  type: "computation" | "storage" | "coordination" | "learning";
  priority: "low" | "normal" | "high" | "critical";
  requirements: TaskRequirements;
  deadline?: number;
  dependencies?: string[];
}

export interface TaskRequirements {
  minNodes: number;
  maxNodes: number;
  requiredCapabilities: string[];
  resourceEstimate: ResourceEstimate;
}

export interface ResourceEstimate {
  cpuCores: number;
  memoryMb: number;
  storageMb?: number;
  networkBandwidthMbps?: number;
}

export interface CoordinationResult {
  taskId: string;
  assignedNodes: string[];
  executionPlan: ExecutionPlan;
  estimatedCompletion: number;
}

export interface ExecutionPlan {
  phases: ExecutionPhase[];
  dataFlow: DataFlow[];
  faultTolerance: FaultToleranceStrategy;
}

export interface ExecutionPhase {
  phaseId: string;
  nodes: string[];
  operation: string;
  dependencies: string[];
}

export interface DataFlow {
  source: string;
  destination: string;
  protocol: "tcp" | "udp" | "grpc" | "http";
  encryption: boolean;
}

export interface FaultToleranceStrategy {
  replicationFactor: number;
  fallbackNodes: string[];
  recoveryProcedure: string;
}

export interface SwarmMetrics {
  totalNodes: number;
  activeNodes: number;
  averagePerformance: number;
  taskThroughput: number;
  coordinationEfficiency: number;
}

export class SwarmCoordinator extends EventEmitter {
  private nodes: Map<string, NodeHandle> = new Map();
  private tasks: Map<string, Task> = new Map();
  private executionPlans: Map<string, ExecutionPlan> = new Map();
  private taskAssignments: Map<string, string[]> = new Map();
  private performanceHistory: Map<string, PerformanceMetrics[]> = new Map();

  constructor() {
    super();
    this.startHealthMonitoring();
    this.startLoadBalancing();
  }

  /**
   * Register a new node in the swarm
   */
  async registerNode(
    nodeInfo: Omit<NodeHandle, "lastSeen" | "performanceMetrics">,
  ): Promise<string> {
    const nodeId = nodeInfo.nodeId || generateNodeId();

    const nodeHandle: NodeHandle = {
      ...nodeInfo,
      nodeId,
      lastSeen: Date.now(),
      performanceMetrics: {
        cpuUsage: 0,
        memoryUsage: 0,
        networkLatency: 0,
        taskCompletionRate: 1.0,
        errorRate: 0,
      },
    };

    this.nodes.set(nodeId, nodeHandle);
    this.performanceHistory.set(nodeId, []);

    this.emit("node_registered", nodeHandle);
    console.log(`[SWARM] Node registered: ${nodeId} (${nodeInfo.address})`);

    return nodeId;
  }

  /**
   * Update node status and metrics
   */
  async updateNodeStatus(nodeId: string, metrics: Partial<PerformanceMetrics>): Promise<boolean> {
    const node = this.nodes.get(nodeId);
    if (!node) return false;

    node.lastSeen = Date.now();
    node.status = this.calculateNodeStatus(metrics);

    // Update metrics
    Object.assign(node.performanceMetrics, metrics);

    // Store in history
    const history = this.performanceHistory.get(nodeId) || [];
    history.push({ ...node.performanceMetrics });

    // Keep only last 100 entries
    if (history.length > 100) {
      history.splice(0, history.length - 100);
    }

    this.performanceHistory.set(nodeId, history);

    this.emit("node_updated", node);
    return true;
  }

  /**
   * Submit a task for coordination
   */
  async coordinateTask(task: Task): Promise<CoordinationResult> {
    // Validate task
    if (!this.validateTask(task)) {
      throw new Error(`Invalid task: ${task.taskId}`);
    }

    // Find suitable nodes
    const suitableNodes = this.findSuitableNodes(task.requirements);

    if (suitableNodes.length < task.requirements.minNodes) {
      throw new Error(`Insufficient nodes available for task ${task.taskId}`);
    }

    // Optimize node assignment
    const assignedNodes = this.optimizeNodeAssignment(
      suitableNodes,
      task.requirements,
      task.priority,
    );

    // Generate execution plan
    const executionPlan = this.generateExecutionPlan(task, assignedNodes);

    // Store coordination result
    this.tasks.set(task.taskId, task);
    this.taskAssignments.set(task.taskId, assignedNodes);
    this.executionPlans.set(task.taskId, executionPlan);

    const result: CoordinationResult = {
      taskId: task.taskId,
      assignedNodes,
      executionPlan,
      estimatedCompletion: Date.now() + this.estimateCompletionTime(task, assignedNodes),
    };

    this.emit("task_coordinated", result);
    return result;
  }

  /**
   * Decompose complex task into subtasks
   */
  async decomposeTask(task: Task): Promise<Task[]> {
    const subtasks: Task[] = [];

    // Simple decomposition strategy - divide by resource requirements
    const resourceChunks = this.chunkResources(task.requirements.resourceEstimate);

    for (let i = 0; i < resourceChunks.length; i++) {
      const subtask: Task = {
        taskId: `${task.taskId}_part_${i}`,
        type: task.type,
        priority: task.priority,
        requirements: {
          ...task.requirements,
          resourceEstimate: resourceChunks[i],
          minNodes: 1,
          maxNodes: Math.max(1, Math.floor(task.requirements.maxNodes / resourceChunks.length)),
        },
        dependencies: i > 0 ? [`${task.taskId}_part_${i - 1}`] : task.dependencies,
        deadline: task.deadline,
      };

      subtasks.push(subtask);
    }

    return subtasks;
  }

  /**
   * Monitor swarm health and performance
   */
  getSwarmMetrics(): SwarmMetrics {
    const nodes = Array.from(this.nodes.values());
    const activeNodes = nodes.filter((n) => n.status === "active");

    const totalPerformance = nodes.reduce(
      (sum, node) => sum + this.calculateNodePerformance(node.performanceMetrics),
      0,
    );

    const averagePerformance = nodes.length > 0 ? totalPerformance / nodes.length : 0;

    return {
      totalNodes: nodes.length,
      activeNodes: activeNodes.length,
      averagePerformance,
      taskThroughput: this.calculateTaskThroughput(),
      coordinationEfficiency: this.calculateCoordinationEfficiency(),
    };
  }

  /**
   * Handle node failures and redistribute tasks
   */
  async handleNodeFailure(failedNodeId: string): Promise<void> {
    console.log(`[SWARM] Handling failure of node: ${failedNodeId}`);

    // Mark node as inactive
    const node = this.nodes.get(failedNodeId);
    if (node) {
      node.status = "inactive";
      this.emit("node_failed", node);
    }

    // Redistribute tasks from failed node
    const affectedTasks = this.findTasksAssignedToNode(failedNodeId);

    for (const taskId of affectedTasks) {
      const task = this.tasks.get(taskId);
      if (task) {
        // Remove failed node from assignment
        const currentAssignment = this.taskAssignments.get(taskId) || [];
        const newAssignment = currentAssignment.filter((id) => id !== failedNodeId);

        // Find replacement nodes
        const replacementNodes = this.findReplacementNodes(task.requirements, newAssignment);

        if (replacementNodes.length > 0) {
          const updatedAssignment = [...newAssignment, ...replacementNodes];
          this.taskAssignments.set(taskId, updatedAssignment);

          // Regenerate execution plan
          const executionPlan = this.generateExecutionPlan(task, updatedAssignment);
          this.executionPlans.set(taskId, executionPlan);

          this.emit("task_redistributed", {
            taskId,
            oldAssignment: currentAssignment,
            newAssignment: updatedAssignment,
          });
        }
      }
    }
  }

  /**
   * Private helper methods
   */
  private calculateNodeStatus(
    metrics: Partial<PerformanceMetrics>,
  ): "active" | "inactive" | "degraded" {
    if (metrics.errorRate && metrics.errorRate > 0.5) return "inactive";
    if (metrics.cpuUsage && metrics.cpuUsage > 90) return "degraded";
    if (metrics.memoryUsage && metrics.memoryUsage > 90) return "degraded";
    return "active";
  }

  private calculateNodePerformance(metrics: PerformanceMetrics): number {
    // Simple weighted performance calculation
    const weights = { cpu: 0.3, memory: 0.2, latency: 0.2, completion: 0.2, error: 0.1 };

    const cpuScore = 1 - metrics.cpuUsage / 100;
    const memoryScore = 1 - metrics.memoryUsage / 100;
    const latencyScore = Math.max(0, 1 - metrics.networkLatency / 1000); // Assume 1000ms max acceptable
    const completionScore = metrics.taskCompletionRate;
    const errorScore = 1 - metrics.errorRate;

    return (
      cpuScore * weights.cpu +
      memoryScore * weights.memory +
      latencyScore * weights.latency +
      completionScore * weights.completion +
      errorScore * weights.error
    );
  }

  private findSuitableNodes(requirements: TaskRequirements): NodeHandle[] {
    return Array.from(this.nodes.values()).filter((node) => {
      if (node.status !== "active") return false;

      // Check capability requirements
      const hasCapabilities = requirements.requiredCapabilities.every((cap) =>
        node.capabilities.includes(cap),
      );

      // Check resource availability (simplified)
      const hasResources =
        node.performanceMetrics.cpuUsage < 80 && node.performanceMetrics.memoryUsage < 80;

      return hasCapabilities && hasResources;
    });
  }

  private optimizeNodeAssignment(
    nodes: NodeHandle[],
    requirements: TaskRequirements,
    priority: Task["priority"],
  ): string[] {
    // Sort nodes by performance and proximity to requirements
    const sortedNodes = [...nodes].sort((a, b) => {
      const perfA = this.calculateNodePerformance(a.performanceMetrics);
      const perfB = this.calculateNodePerformance(b.performanceMetrics);

      // Higher priority tasks get better performing nodes
      const priorityBoost = priority === "critical" ? 0.2 : priority === "high" ? 0.1 : 0;

      return perfB + priorityBoost - (perfA + priorityBoost);
    });

    const numNodes = Math.min(
      requirements.maxNodes,
      Math.max(requirements.minNodes, Math.ceil(sortedNodes.length * 0.6)),
    );

    return sortedNodes.slice(0, numNodes).map((n) => n.nodeId);
  }

  private generateExecutionPlan(task: Task, assignedNodes: string[]): ExecutionPlan {
    const phases: ExecutionPhase[] = [];
    const dataFlows: DataFlow[] = [];

    // Simple linear execution plan
    for (let i = 0; i < assignedNodes.length; i++) {
      phases.push({
        phaseId: `phase_${i}`,
        nodes: [assignedNodes[i]],
        operation: `execute_${task.type}`,
        dependencies: i > 0 ? [`phase_${i - 1}`] : [],
      });

      // Add data flow between consecutive phases
      if (i > 0) {
        dataFlows.push({
          source: assignedNodes[i - 1],
          destination: assignedNodes[i],
          protocol: "grpc",
          encryption: true,
        });
      }
    }

    return {
      phases,
      dataFlow: dataFlows,
      faultTolerance: {
        replicationFactor: Math.min(3, assignedNodes.length),
        fallbackNodes: assignedNodes.slice(0, Math.min(2, assignedNodes.length)),
        recoveryProcedure: "retry_with_fallback",
      },
    };
  }

  private chunkResources(resources: ResourceEstimate): ResourceEstimate[] {
    const chunks: ResourceEstimate[] = [];
    const numChunks = Math.max(2, Math.floor(resources.cpuCores / 2));

    for (let i = 0; i < numChunks; i++) {
      chunks.push({
        cpuCores: Math.ceil(resources.cpuCores / numChunks),
        memoryMb: Math.ceil(resources.memoryMb / numChunks),
        storageMb: resources.storageMb ? Math.ceil(resources.storageMb / numChunks) : undefined,
        networkBandwidthMbps: resources.networkBandwidthMbps
          ? Math.ceil(resources.networkBandwidthMbps / numChunks)
          : undefined,
      });
    }

    return chunks;
  }

  private estimateCompletionTime(task: Task, nodes: string[]): number {
    // Simplified estimation based on resource requirements and node performance
    const baseTime = task.requirements.resourceEstimate.cpuCores * 1000; // ms per core
    const nodePerformance =
      nodes.reduce((sum, nodeId) => {
        const node = this.nodes.get(nodeId);
        return sum + (node ? this.calculateNodePerformance(node.performanceMetrics) : 0.5);
      }, 0) / nodes.length;

    return baseTime / (nodePerformance || 0.5);
  }

  private validateTask(task: Task): boolean {
    return (
      task.requirements.minNodes <= task.requirements.maxNodes &&
      task.requirements.minNodes > 0 &&
      task.requirements.resourceEstimate.cpuCores > 0 &&
      task.requirements.resourceEstimate.memoryMb > 0
    );
  }

  private findTasksAssignedToNode(nodeId: string): string[] {
    const result: string[] = [];
    for (const [taskId, assignment] of this.taskAssignments.entries()) {
      if (assignment.includes(nodeId)) {
        result.push(taskId);
      }
    }
    return result;
  }

  private findReplacementNodes(requirements: TaskRequirements, exclude: string[]): string[] {
    const suitable = this.findSuitableNodes(requirements);
    return suitable
      .filter((node) => !exclude.includes(node.nodeId))
      .slice(0, requirements.minNodes)
      .map((node) => node.nodeId);
  }

  private calculateTaskThroughput(): number {
    // Simplified calculation
    return this.tasks.size / (Object.keys(this.nodes).length || 1);
  }

  private calculateCoordinationEfficiency(): number {
    // Simplified efficiency metric
    const totalAssignments = Array.from(this.taskAssignments.values()).flat().length;
    const totalPossible = this.tasks.size * 3; // Assume avg 3 nodes per task
    return totalPossible > 0 ? totalAssignments / totalPossible : 1;
  }

  private startHealthMonitoring() {
    setInterval(() => {
      const now = Date.now();
      for (const [nodeId, node] of this.nodes.entries()) {
        // Mark nodes as inactive if not seen for 30 seconds
        if (now - node.lastSeen > 30000) {
          if (node.status !== "inactive") {
            this.handleNodeFailure(nodeId);
          }
        }
      }
    }, 10000); // Check every 10 seconds
  }

  private startLoadBalancing() {
    setInterval(() => {
      // Simple load balancing - redistribute overloaded nodes
      const overloadedNodes = Array.from(this.nodes.values()).filter(
        (node) => node.performanceMetrics.cpuUsage > 80 || node.performanceMetrics.memoryUsage > 80,
      );

      for (const node of overloadedNodes) {
        this.redistributeNodeLoad(node.nodeId);
      }
    }, 30000); // Balance every 30 seconds
  }

  private async redistributeNodeLoad(nodeId: string): Promise<void> {
    const tasks = this.findTasksAssignedToNode(nodeId);
    // In a real implementation, this would migrate tasks to other nodes
    console.log(`[SWARM] Redistributing load from node ${nodeId} (${tasks.length} tasks)`);
  }
}

// Singleton instance
let swarmCoordinator: SwarmCoordinator | null = null;

export function getSwarmCoordinator(): SwarmCoordinator {
  if (!swarmCoordinator) {
    swarmCoordinator = new SwarmCoordinator();
  }
  return swarmCoordinator;
}
