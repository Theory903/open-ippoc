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
    
    # 1. Initialize proprioception system (Phase 1: Spine Connection)
    print("[IPPOC] Initializing bio-digital proprioception system...")
    try:
        import asyncio
        # Run async scanner
        async def scan_wrapper():
            from cortex.gateway.proprioception_scanner import get_scanner
            scanner = get_scanner()
            return await scanner.scan_skills()
        
        skills = asyncio.run(scan_wrapper())
        print(f"[IPPOC] Proprioception mapped {len(skills)} OpenClaw skills")
    except Exception as e:
        print(f"[IPPOC] Warning: Proprioception scan failed: {e}")
    
    # 2. Initialize synapse bridge to OpenClaw kernel
    print("[IPPOC] Establishing synapse bridge to OpenClaw kernel...")
    try:
        # Run in background task
        import threading
        def start_bridge():
            asyncio.run(initialize_synapse_bridge())
        bridge_thread = threading.Thread(target=start_bridge, daemon=True)
        bridge_thread.start()
        print("[IPPOC] Synapse bridge initialization started")
    except Exception as e:
        print(f"[IPPOC] Warning: Synapse bridge init failed: {e}")
    
    # 3. Start heartbeat monitor
    try:
        import threading
        def start_heartbeat():
            asyncio.run(heartbeat_monitor())
        heartbeat_thread = threading.Thread(target=start_heartbeat, daemon=True)
        heartbeat_thread.start()
        print("[IPPOC] Heartbeat monitor started")
    except Exception as e:
        print(f"[IPPOC] Warning: Heartbeat monitor failed: {e}")
    
    # 4. Register Core Tools (Original functionality)
    print("[IPPOC] Registering core cognitive tools...")
    
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
    
    print("[IPPOC] Core Tools Registered: Memory, Body, Evolution, Research, Simulation, Social, Maintainer, Economy, Earnings")
    print("[IPPOC] Bio-digital integration layer active")
