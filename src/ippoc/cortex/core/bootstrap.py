import sys
import os
from ippoc.cortex.core.orchestrator import get_orchestrator
from ippoc.cortex.core.tools.memory import MemoryAdapter
from ippoc.cortex.core.tools.body import BodyAdapter
from ippoc.cortex.core.tools.evolution import EvolutionAdapter
from ippoc.cortex.core.tools.cerebellum import CerebellumAdapter
from ippoc.cortex.core.tools.worldmodel import WorldModelAdapter
from ippoc.cortex.core.tools.social import SocialAdapter
from ippoc.cortex.core.tools.maintainer import MaintainerAdapter
from ippoc.cortex.core.tools.economy import EconomyAdapter
from ippoc.cortex.core.tools.earnings import EarningsAdapter
from ippoc.cortex.plugins.native.shell import NativeShellAdapter

# Enhanced imports for bio-digital integration (Lazy loaded)
import asyncio
import importlib

def _try_load_openclaw():
    """Attempt to load the OpenClaw plugin only if explicitly enabled."""
    if os.getenv("IPPOC_ENABLE_OPENCLAW", "false").lower() != "true":
        return None
        
    try:
        adapter = importlib.import_module("ippoc.cortex.plugins.openclaw.openclaw_adapter")
        return adapter
    except ImportError:
        print("[IPPOC] OpenClaw plugin not found, skipping synapse bridge", file=sys.stderr)
        return None

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
        openclaw = _try_load_openclaw()
        if not openclaw:
            return

        try:
            # Synapse bridge initialization (Proprioception is now lazy-loaded by tools)
            print("[IPPOC] Establishing synapse bridge to OpenClaw kernel...", file=sys.stderr)
            await openclaw.initialize_synapse_bridge()
            print("[IPPOC] Synapse bridge initialization complete", file=sys.stderr)
            
            # Start heartbeat monitor in background
            asyncio.create_task(openclaw.heartbeat_monitor())
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

    # Register Native Shell (Self-Sustaining Actor)
    orc.register(NativeShellAdapter())
    
    print("[IPPOC] Core Tools Registered: Memory, Body, Evolution, Research, Simulation, Social, Maintainer, Economy, Earnings", file=sys.stderr)
    print("[IPPOC] Bio-digital integration layer active", file=sys.stderr)
