from typing import TypedDict, List, Annotated, Optional
import operator
from cortex.core.orchestrator import get_orchestrator
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.cortex.two_tower import TwoTowerEngine
from cortex.cortex.telepathy import TelepathySwarm
from cortex.cortex.schemas import CognitiveState, Signal
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Prototyping Mock if dependency missing
    class StateGraph:
        def __init__(self, state_schema): pass
        def add_node(self, name, func): pass
        def add_edge(self, start, end): pass
        def set_entry_point(self, name): pass
        def compile(self): return "compiled_graph_stub"
    END = "END"

class LangGraphEngine:
    """
    The Brainstem: Orchestrates the cognitive loop.
    Graph Topology:
    Observe -> Score -> Inner Voice -> Validate -> Execute -> Learn
    """
    def __init__(self, two_tower: TwoTowerEngine, swarm: TelepathySwarm):
        self.tt = two_tower
        self.swarm = swarm
        self.graph = self._build_graph()
        self.orchestrator = get_orchestrator()

    def _build_graph(self):
        """
        Constructs the StateGraph.
        """
        workflow = StateGraph(CognitiveState)
        
        # Nodes
        workflow.add_node("observe", self.observe)
        workflow.add_node("inner_voice", self.inner_voice)
        workflow.add_node("validate", self.validate)
        workflow.add_node("execute", self.execute)
        
        # Edges (Simple Sequential Topology)
        workflow.set_entry_point("observe")
        workflow.add_edge("observe", "inner_voice")
        workflow.add_edge("inner_voice", "validate")
        workflow.add_edge("validate", "execute")
        workflow.add_edge("execute", END)
        
        return workflow.compile()

    async def observe(self, state: CognitiveState):
        """
        Ingest signals from Body (OpenClaw) and Telepathy.
        """
        # Logic to fetch latest signals
        return {"signals": []}

    async def inner_voice(self, state: CognitiveState):
        """
        Tower A: Generate hypotheses.
        """
        context = state.get("memory_context", "") + str(state.get("signals", []))
        impulse = await self.tt.generate_impulse(context)
        return {
            "proposed_action": impulse, 
            "inner_monologue": [f"Impulse: {impulse.payload.get('thought')}"]
        }

    async def validate(self, state: CognitiveState):
        """
        Tower B: Check constraints if risky.
        """
        action = state.get("proposed_action")
        if not action:
            return {}
            
        approved = await self.tt.validate_action(action)
        if not approved:
             return {"proposed_action": None, "inner_monologue": ["Validator rejected action."]}
        return {}

    async def execute(self, state: CognitiveState):
        """
        Send command to Body via Tool Orchestrator.
        """
        action = state.get("proposed_action")
        if not action:
            return {}
        
        # Construct Envelope
        envelope = ToolInvocationEnvelope(
            tool_name="body", # Or map specific tool from action string
            domain="body",
            action=action.action, # e.g. "execute_command"
            context={
                "params": action.payload or {},
                "caller": "langgraph.brainstem",
                "source": "cortex"
            },
            risk_level="medium", # TODO: Dynamic risk
            estimated_cost=0.0 # Orchestrator handles this via tool.estimate_cost
        )
        
        try:
            result = self.orchestrator.invoke(envelope)
            return {"execution_result": str(result.output) if result.success else f"FAIL: {result.warnings}"}
        except Exception as e:
            print(f"[EXECUTE-FAIL] Orchestrator Rejected: {e}")
            return {"execution_result": f"Failed: {e}"}

    async def run_step(self, input_signal: Signal):
        """
        Manually stepping through the logic until LangGraph is active.
        """
        state: CognitiveState = {
            "signals": [input_signal],
            "memory_context": "",
            "inner_monologue": [],
            "proposed_action": None,
            "execution_result": None
        }
        
        # 1. Observe
        await self.observe(state)
        
        # 2. Inner Voice (Tower A)
        voice_update = await self.inner_voice(state)
        state.update(voice_update) # type: ignore
        
        # 3. Validate (Tower B)
        val_update = await self.validate(state)
        state.update(val_update) # type: ignore
        
        # 4. Execute
        if state["proposed_action"]:
            exec_update = await self.execute(state)
            state.update(exec_update) # type: ignore
            
        return state
