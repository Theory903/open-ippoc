from brain.core.orchestrator import get_orchestrator
from brain.core.tools.memory import MemoryAdapter
from brain.core.tools.body import BodyAdapter
from brain.core.tools.evolution import EvolutionAdapter
from brain.core.tools.cerebellum import CerebellumAdapter
from brain.core.tools.worldmodel import WorldModelAdapter
from brain.core.tools.social import SocialAdapter
from brain.core.tools.maintainer import MaintainerAdapter
from brain.core.tools.economy import EconomyAdapter

def bootstrap_tools():
    """
    Initializes the Tool Orchestrator with default IPPOC domain adapters.
    This must be called at system startup (e.g., in server.py).
    """
    orc = get_orchestrator()
    
    # Register Memory Tool
    orc.register(MemoryAdapter())
    
    # Register Body Tool
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
    
    print("[IPPOC] Core Tools Registered: Memory, Body, Evolution, Research, Simulation, Social, Maintainer, Economy")
