import sys
from cortex.core.orchestrator import get_orchestrator
from cortex.core.tools.memory import MemoryAdapter
from cortex.core.tools.body import BodyAdapter
from cortex.core.tools.evolution import EvolutionAdapter
from cortex.core.tools.cerebellum import CerebellumAdapter
from cortex.core.tools.worldmodel import WorldModelAdapter
from cortex.core.tools.social import SocialAdapter
from cortex.core.tools.maintainer import MaintainerAdapter
from cortex.core.tools.economy import EconomyAdapter
from cortex.core.tools.earnings import EarningsAdapter

# Enhanced imports for bio-digital integration
from cortex.gateway.proprioception_scanner import scan_and_register_skills
from cortex.gateway.openclaw_adapter import initialize_synapse_bridge, heartbeat_monitor
import asyncio

def bootstrap_tools():
    """
    Initializes the Tool Orchestrator with default IPPOC domain adapters.
    This must be called at system startup (e.g., in server.py).
    Enhanced with bio-digital integration.
    """
    orc = get_orchestrator()
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    # 1. Initialize proprioception system (Phase 1: Spine Connection)
    print("[IPPOC] Initializing bio-digital proprioception system...", file=sys.stderr)
    
    async def run_bootstrap_async():
        try:
            # Synapse bridge initialization (Proprioception is now lazy-loaded by tools)
            print("[IPPOC] Establishing synapse bridge to OpenClaw kernel...", file=sys.stderr)
            await initialize_synapse_bridge()
            print("[IPPOC] Synapse bridge initialization complete", file=sys.stderr)
            
            # Start heartbeat monitor in background
            asyncio.create_task(heartbeat_monitor())
            print("[IPPOC] Heartbeat monitor started", file=sys.stderr)
            
        except Exception as e:
            print(f"[IPPOC] Bio-digital integration initialization failed: {e}", file=sys.stderr)

    if loop:
        loop.create_task(run_bootstrap_async())
    else:
        # Fallback for non-async contexts if any
        import threading
        def _run_in_thread():
             asyncio.run(run_bootstrap_async())
        threading.Thread(target=_run_in_thread, daemon=True).start()
    
    print("[IPPOC] Synapse bridge and proprioception tasks scheduled", file=sys.stderr)
    
    # 4. Register Core Tools (Original functionality)
    print("[IPPOC] Registering core cognitive tools...", file=sys.stderr)
    
    # Register Memory Tool
    orc.register(MemoryAdapter())
    
    # Register Enhanced Body Tool (now with OpenClaw integration)
    orc.register(BodyAdapter())
    
    # Register Evolution Tool
    orc.register(EvolutionAdapter())
    
    # Register Research Tool (Cerebellum)
    orc.register(CerebellumAdapter())
    
    # Register Simulation Tool (WorldModel)
    orc.register(WorldModelAdapter())

    # Register Social Tool
    orc.register(SocialAdapter())

    # Register Maintainer Tool
    orc.register(MaintainerAdapter())

    # Register Economy Tool
    orc.register(EconomyAdapter())
    
    # Register Earnings Tool (NEW: Real value generation)
    orc.register(EarningsAdapter())
    
    print("[IPPOC] Core Tools Registered: Memory, Body, Evolution, Research, Simulation, Social, Maintainer, Economy, Earnings", file=sys.stderr)
    print("[IPPOC] Bio-digital integration layer active", file=sys.stderr)
