export * from "./identity/index.js";
export * from "./execution/capability-tokens.js";
export * from "./execution/fs-rooting.js";
export * from "./execution/wasm-gate.js";
export * from "./evolution/dry-run.js";
export * from "./evolution/conflict-mediator.js";
export * from "./evolution/canon-scan.js";
export * from "./physiology/pain-aggregator.js";
export * from "./physiology/sidecar-orchestrator.js";
export * from "./physiology/organ-health.js";
export * from "./cognition/opportunity-detector.js";
export * from "./cognition/strategic-refactor.js";
export * from "./cognition/vision-memory.js";
export * from "./cognition/founder-loop.js";
export * from "./cognition/market-sensing.js";
export * from "./cognition/advanced-capabilities.js";
export * from "./evolution/self-hiring.js";
export * from "./lifecycle/state-machine.js";
export * from "./lifecycle/health-coordinator.js";
export * from "./lifecycle/permission-gates.js";

import {
  AutonomousResearch,
  PatternMiner,
  CompetitiveAnalyzer,
  BehaviorPredictor,
} from "./cognition/advanced-capabilities.js";
import { FounderLoop } from "./cognition/founder-loop.js";
import { OpportunityDetector } from "./cognition/opportunity-detector.js";
import { StrategicRefactor } from "./cognition/strategic-refactor.js";
import { VisionMemory } from "./cognition/vision-memory.js";
import { FederatedLearning } from "./collective/federated-learning.js";
import { SwarmCoordinator } from "./collective/swarm-coordinator.js";
import { CreativeSolver } from "./creative/creative-solver.js";
import { EmotionRecognition } from "./emotional/emotion-recognition.js";
import { SocialDynamicsAnalyzer } from "./emotional/social-dynamics.js";
import { CanonScanner } from "./evolution/canon-scan.js";
import { ConflictMediator } from "./evolution/conflict-mediator.js";
import { DryRunEngine } from "./evolution/dry-run.js";
import { GovernanceValidator } from "./evolution/governance-validator.js";
import { CapabilityTokenManager } from "./execution/capability-tokens.js";
import { NodeRootManager } from "./execution/fs-rooting.js";
import { ResourceLimits } from "./execution/resource-limits.js";
import { WASMGate } from "./execution/wasm-gate.js";
import { MeshCoordinator } from "./identity/mesh-coordinator.js";
import { ReplayCache } from "./identity/replay-cache.js";
import { SovereignHandshake } from "./identity/sovereign-handshake.js";
import { TrustStateMachine } from "./identity/trust-state-machine.js";
import { HealthCoordinator } from "./lifecycle/health-coordinator.js";
import { PermissionGates } from "./lifecycle/permission-gates.js";
import { LifecycleStateMachine } from "./lifecycle/state-machine.js";
import { OrganHealth } from "./physiology/organ-health.js";
import { PainAggregator } from "./physiology/pain-aggregator.js";
import { SidecarOrchestrator } from "./physiology/sidecar-orchestrator.js";

export class HAL {
  public identity: {
    handshake: SovereignHandshake;
    trustMachine: TrustStateMachine;
    replayCache: ReplayCache;
    mesh: MeshCoordinator;
  };
  public execution: {
    tokens: CapabilityTokenManager;
    fsRoot: NodeRootManager;
    wasmGate: WASMGate;
    limits: ResourceLimits;
  };
  public evolution: {
    dryRun: DryRunEngine;
    conflictMediator: ConflictMediator;
    canonScanner: CanonScanner;
    governance: GovernanceValidator;
  };
  public physiology: {
    pain: PainAggregator;
    sidecars: SidecarOrchestrator;
    health: OrganHealth;
  };
  public cognition: {
    opportunity: OpportunityDetector;
    refactor: StrategicRefactor;
    memory: VisionMemory;
    founderLoop: FounderLoop;
    research: AutonomousResearch;
    mining: PatternMiner;
    strategy: CompetitiveAnalyzer;
    prediction: BehaviorPredictor;
  };
  public lifecycle: {
    state: LifecycleStateMachine;
    health: HealthCoordinator;
    gates: PermissionGates;
  };
  public collective: {
    swarm: SwarmCoordinator;
    federated: FederatedLearning;
  };
  public emotional: {
    emotion: EmotionRecognition;
    social: SocialDynamicsAnalyzer;
  };
  public creative: {
    solver: CreativeSolver;
  };

  private static instance: HAL;

  private constructor() {
    // Identity
    const trustMachine = new TrustStateMachine();
    const replayCache = new ReplayCache();
    // Default placeholder keypair - in prod, load from secure storage
    const keypair = {
      privateKey: new Uint8Array(32),
      publicKey: new Uint8Array(32),
    };
    const handshake = new SovereignHandshake({ keypair, trustMachine, replayCache });
    const mesh = new MeshCoordinator(trustMachine);

    this.identity = { handshake, trustMachine, replayCache, mesh };

    // Execution
    const tokens = new CapabilityTokenManager();
    const fsRoot = new NodeRootManager();
    const wasmGate = new WASMGate(tokens);
    const limits = new ResourceLimits();
    this.execution = { tokens, fsRoot, wasmGate, limits };

    // Evolution
    const dryRun = new DryRunEngine();
    const conflictMediator = new ConflictMediator();
    const canonScanner = new CanonScanner();
    const governance = new GovernanceValidator(canonScanner);
    this.evolution = { dryRun, conflictMediator, canonScanner, governance };

    // Physiology
    const pain = new PainAggregator();
    const sidecars = new SidecarOrchestrator();
    const health = new OrganHealth();
    this.physiology = { pain, sidecars, health };

    // Cognition
    const opportunity = new OpportunityDetector();
    const refactor = new StrategicRefactor();
    const memory = new VisionMemory();
    const founderLoop = new FounderLoop(opportunity, refactor, memory);

    // Advanced Cognition (Appendix B)
    const research = new AutonomousResearch();
    const mining = new PatternMiner();
    const strategy = new CompetitiveAnalyzer();
    const prediction = new BehaviorPredictor();

    this.cognition = {
      opportunity,
      refactor,
      memory,
      founderLoop,
      research,
      mining,
      strategy,
      prediction,
    };

    // Lifecycle (Appendix A)
    const state = new LifecycleStateMachine();
    const healthCoord = new HealthCoordinator(state, pain);
    const gates = new PermissionGates(tokens);
    this.lifecycle = { state, health: healthCoord, gates };

    // Collective Intelligence (Phase 10)
    const swarm = new SwarmCoordinator();
    const federated = new FederatedLearning();
    this.collective = { swarm, federated };

    // Emotional Intelligence (Phase 11)
    const emotion = new EmotionRecognition();
    const social = new SocialDynamicsAnalyzer();
    this.emotional = { emotion, social };

    // Creative Capabilities (Phase 12)
    const solver = new CreativeSolver();
    this.creative = { solver };

    // Start the Founder Loop (in a real system, this would be a scheduled task)
    // For now, we just fire-and-forget one cycle to warm it up
    founderLoop.founderModeCycle().catch(console.error);
  }

  public static getInstance(): HAL {
    if (!HAL.instance) {
      HAL.instance = new HAL();
    }
    return HAL.instance;
  }
}
