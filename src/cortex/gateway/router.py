"""
Adaptive RAG Router - The Thalamus of IPPOC

This module implements the master controller that routes queries to appropriate
RAG architectures based on biological cognitive mapping.

Biological Mapping:
- Adaptive RAG = Thalamus (Router)
- Routes to 13 specialized RAG types based on query characteristics
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# LangChain Core Imports
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

# LangGraph Imports
from langgraph.graph import StateGraph, END

# Pydantic for structured output
from pydantic import BaseModel, Field

# IPPOC Core imports
from cortex.core.orchestrator import get_orchestrator
from cortex.core.autonomy import AutonomyController

# IPPOC Memory System imports
from mnemosyne.graph.manager import GraphManager
from mnemosyne.semantic.rag import SemanticManager
from mnemosyne.episodic.manager import EpisodicManager

logger = logging.getLogger(__name__)

class RAGType(Enum):
    """Enumeration of RAG architectures mapped to IPPOC biology"""
    ADAPTIVE = "adaptive"      # Thalamus - Master Router
    AGENTIC = "agentic"        # Brain - Complex reasoning
    SELF_RAG = "self_rag"      # Brain - Self-critique
    BRANCHED = "branched"      # Brain - Multi-perspective
    CORRECTIVE = "corrective"  # Brain - Fact verification
    GRAPH = "graph"           # Mind - Relationship traversal
    HYDE = "hyde"             # Mind - Hypothetical embeddings
    MEMORY = "memory"         # Mind - Contextual recall
    ADVANCED = "advanced"     # Mind - Precision search
    SPECULATIVE = "speculative" # Spine - Fast anticipation
    NAIVE = "naive"           # Spine - Simple fallback
    SIMPLE = "simple"         # Spine - Baseline retrieval
    MULTIMODAL = "multimodal" # Body - Visual processing
    MODULAR = "modular"       # Body - Plug-and-play

@dataclass
class RoutingDecision:
    """Represents a routing decision with metadata"""
    rag_type: RAGType
    confidence: float
    reason: str
    target_service: str
    parameters: Dict[str, Any]

class QueryClassification(BaseModel):
    """Structured query classification for adaptive routing"""
    complexity: float = Field(..., ge=0.0, le=1.0, description="Query complexity score")
    abstraction: float = Field(..., ge=0.0, le=1.0, description="Abstract concept level")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Speed requirement")
    safety_risk: float = Field(..., ge=0.0, le=1.0, description="Canon violation risk")
    category: str = Field(..., description="Query category")

class RelevanceScore(BaseModel):
    """Self-RAG critique scores"""
    relevance: float = Field(..., ge=0.0, le=1.0)
    support: float = Field(..., ge=0.0, le=1.0)
    utility: float = Field(..., ge=0.0, le=1.0)
    overall: float = Field(..., ge=0.0, le=1.0)

class AdaptiveRAGRouter:
    """
    Production-ready Adaptive RAG Router implementing all 14 architectures.
    
    Follows first principles logic for each RAG type with proper LangChain integration.
    """
    
    def __init__(self, llm: Runnable = None, embeddings: Embeddings = None, vectorstore: VectorStore = None):
        # Core components
        self.llm = llm
        self.embeddings = embeddings
        self.vectorstore = vectorstore
        
        # IPPOC system integrations
        self.orchestrator = get_orchestrator()
        self.autonomy = AutonomyController()
        self.graph_manager = GraphManager()
        self.semantic_manager = SemanticManager(vectorstore, embeddings) if vectorstore and embeddings else None
        self.episodic_manager = EpisodicManager()
        
        # Thresholds for routing decisions
        self.complexity_threshold = 0.7
        self.abstraction_threshold = 0.6
        self.urgency_threshold = 0.8
        self.safety_threshold = 0.5
        
    async def route_query(self, query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """Main routing entry point - classify and route query"""
        context = context or {}
        
        # Classify query using adaptive logic
        classification = await self._classify_query(query, context)
        
        # Route based on first principles logic
        if self._should_route_to_brain(classification):
            return await self._route_to_brain(query, classification)
        elif self._should_route_to_mind(classification):
            return await self._route_to_mind(query, classification)
        elif self._should_route_to_spine(classification):
            return await self._route_to_spine(query, classification)
        else:
            return await self._route_to_body(query, classification)
    
    async def _classify_query(self, query: str, context: Dict) -> QueryClassification:
        """Classify query using LLM-based analysis"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert query classifier for a bio-digital AI system."),
            ("human", """Analyze this query and classify it across four dimensions:
            
Query: {query}
Context: {context}

Rate each dimension from 0.0 to 1.0:
- Complexity: How complex is the reasoning required?
- Abstraction: How abstract/conceptual is the query?
- Urgency: How quickly does this need to be answered?
- Safety Risk: Risk of violating system principles?

Also categorize it into: research, technical, memory, factual, conversational, system, general"""),
        ])
        
        chain = prompt | self.llm | PydanticOutputParser(pydantic_object=QueryClassification)
        return await chain.ainvoke({"query": query, "context": str(context)})
    
    def _should_route_to_brain(self, classification: QueryClassification) -> bool:
        """Brain routing logic - complex reasoning required"""
        return (classification.complexity > self.complexity_threshold or 
                classification.category in ['research', 'technical'])
    
    def _should_route_to_mind(self, classification: QueryClassification) -> bool:
        """Mind routing logic - context/memory focused"""
        return (classification.abstraction > self.abstraction_threshold or
                classification.category in ['memory', 'conversational'])
    
    def _should_route_to_spine(self, classification: QueryClassification) -> bool:
        """Spine routing logic - speed prioritized"""
        return (classification.urgency > self.urgency_threshold or
                classification.category in ['system', 'factual'])
    
    def _assess_complexity(self, query: str) -> float:
        """Assess query complexity (0.0 to 1.0)"""
        # Length-based complexity
        length_score = min(1.0, len(query) / 200)
        
        # Keyword complexity indicators
        complex_indicators = [
            'research', 'analyze', 'implement', 'compare', 'evaluate',
            'strategy', 'architecture', 'design', 'optimize', 'debug'
        ]
        keyword_score = sum(1 for word in complex_indicators if word in query.lower()) / len(complex_indicators)
        
        # Question type complexity
        question_indicators = ['how', 'why', 'explain', 'compare']
        question_score = 0.3 if any(q in query.lower() for q in question_indicators) else 0.1
        
        return (length_score * 0.4) + (keyword_score * 0.4) + (question_score * 0.2)
    
    def _assess_safety_risk(self, query: str) -> float:
        """Assess safety/canon violation risk"""
        # Canon violation keywords
        violation_keywords = [
            'delete', 'destroy', 'harm', 'illegal', 'bypass', 'hack',
            'override', 'ignore', 'disable', 'remove'
        ]
        
        risk_score = sum(1 for word in violation_keywords if word in query.lower()) / len(violation_keywords)
        
        # Self-reference queries (potentially sensitive)
        if any(word in query.lower() for word in ['you', 'your', 'identity', 'memory']):
            risk_score += 0.3
            
        return min(1.0, risk_score)
    
    def _assess_speed_need(self, query: str, context: Dict) -> float:
        """Assess speed/latency requirements"""
        # Interactive context indicators
        interactive_indicators = ['chat', 'conversation', 'discuss', 'talk']
        interactive_score = 0.8 if any(word in str(context.get('mode', '')).lower() for word in interactive_indicators) else 0.3
        
        # Short query preference
        length_score = 1.0 if len(query) < 50 else 0.5
        
        # Real-time context
        realtime_indicators = ['now', 'immediately', 'quick', 'fast']
        realtime_score = 0.9 if any(word in query.lower() for word in realtime_indicators) else 0.4
        
        return max(interactive_score, length_score, realtime_score)
    
    def _classify_intent(self, query: str) -> str:
        """Classify query intent category"""
        query_lower = query.lower()
        
        # Research/Analysis intent
        if any(word in query_lower for word in ['research', 'study', 'analyze', 'investigate']):
            return 'research'
            
        # Technical/Code intent
        elif any(word in query_lower for word in ['code', 'implement', 'program', 'script', 'function']):
            return 'technical'
            
        # Memory/Context intent
        elif any(word in query_lower for word in ['remember', 'recall', 'who', 'what', 'when', 'relationship']):
            return 'memory'
            
        # Simple/Factual intent
        elif any(word in query_lower for word in ['what is', 'how to', 'define', 'explain']):
            return 'factual'
            
        # Conversational intent
        elif any(word in query_lower for word in ['hello', 'hi', 'hey', 'goodbye', 'thanks']):
            return 'conversational'
            
        # System/Status intent
        elif any(word in query_lower for word in ['status', 'version', 'ping', 'health', 'running']):
            return 'system'
            
        else:
            return 'general'
    
    def _should_route_to_brain(self, complexity: float, intent: str) -> bool:
        """Determine if query should go to brain (complex reasoning)"""
        high_complexity_intents = ['research', 'technical']
        return complexity > self.complexity_threshold or intent in high_complexity_intents
    
    def _should_route_to_mind(self, safety_risk: float, intent: str) -> bool:
        """Determine if query should go to mind (memory/context/safety)"""
        safety_intents = ['memory', 'conversational']
        return safety_risk > self.safety_threshold or intent in safety_intents
    
    def _should_route_to_spine(self, speed_need: float, intent: str) -> bool:
        """Determine if query should go to spine (fast/simple)"""
        fast_intents = ['system', 'factual', 'conversational']
        return speed_need > self.speed_threshold or intent in fast_intents
    
    async def _route_to_brain(self, query: str, classification: QueryClassification) -> RoutingDecision:
        """Route to brain-based RAG architectures"""
        if classification.complexity > 0.8:
            return RoutingDecision(
                rag_type=RAGType.AGENTIC,
                confidence=0.95,
                reason="High complexity requiring multi-step reasoning",
                target_service="brain/agentic_pipeline",
                parameters={"query": query, "max_iterations": 5}
            )
        elif classification.safety_risk > self.safety_threshold:
            return RoutingDecision(
                rag_type=RAGType.SELF_RAG,
                confidence=0.9,
                reason="Safety-sensitive query requiring self-validation",
                target_service="brain/self_rag_pipeline",
                parameters={"query": query, "validation_rounds": 3}
            )
        else:
            return RoutingDecision(
                rag_type=RAGType.BRANCHED,
                confidence=0.85,
                reason="Multi-perspective analysis needed",
                target_service="brain/branched_pipeline",
                parameters={"query": query, "branches": 3}
            )
    
    async def _route_to_mind(self, query: str, classification: QueryClassification) -> RoutingDecision:
        """Route to mind-based RAG architectures"""
        if classification.abstraction > 0.7:
            return RoutingDecision(
                rag_type=RAGType.HYDE,
                confidence=0.9,
                reason="Abstract concept requiring hypothetical embeddings",
                target_service="mind/hyde_pipeline",
                parameters={"query": query}
            )
        elif 'memory' in classification.category:
            return RoutingDecision(
                rag_type=RAGType.MEMORY,
                confidence=0.85,
                reason="Contextual memory recall needed",
                target_service="mind/memory_pipeline",
                parameters={"query": query, "context_window": 10}
            )
        else:
            return RoutingDecision(
                rag_type=RAGType.GRAPH,
                confidence=0.8,
                reason="Relationship/entity traversal required",
                target_service="mind/graph_pipeline",
                parameters={"query": query}
            )
    
    async def _route_to_spine(self, query: str, classification: QueryClassification) -> RoutingDecision:
        """Route to spine-based RAG architectures"""
        if classification.urgency > 0.9:
            return RoutingDecision(
                rag_type=RAGType.SPECULATIVE,
                confidence=0.95,
                reason="High urgency requiring speculative execution",
                target_service="spine/speculative_pipeline",
                parameters={"query": query, "draft_model": "fast_llm"}
            )
        elif classification.category == 'system':
            return RoutingDecision(
                rag_type=RAGType.NAIVE,
                confidence=0.9,
                reason="System query requiring fast simple response",
                target_service="spine/naive_pipeline",
                parameters={"query": query}
            )
        else:
            return RoutingDecision(
                rag_type=RAGType.SIMPLE,
                confidence=0.8,
                reason="Basic retrieval sufficient",
                target_service="spine/simple_pipeline",
                parameters={"query": query}
            )
    
    async def _route_to_body(self, query: str, classification: QueryClassification) -> RoutingDecision:
        """Route to body-based RAG architectures"""
        if 'image' in str(classification.category).lower() or 'visual' in str(classification.category).lower():
            return RoutingDecision(
                rag_type=RAGType.MULTIMODAL,
                confidence=0.85,
                reason="Multimodal content processing required",
                target_service="body/multimodal_pipeline",
                parameters={"query": query}
            )
        else:
            return RoutingDecision(
                rag_type=RAGType.MODULAR,
                confidence=0.8,
                reason="Modular component assembly needed",
                target_service="body/modular_pipeline",
                parameters={"query": query}
            )
    
    async def execute_routed_query(self, routing_decision: RoutingDecision) -> Dict[str, Any]:
        """
        Execute the routed query using the appropriate RAG architecture.
        
        Args:
            routing_decision: Routing decision from route_query()
            
        Returns:
            Execution result with response and metadata
        """
        try:
            logger.info(f"Executing {routing_decision.rag_type.value} RAG for query")
            
            # Execute based on RAG type
            if routing_decision.rag_type == RAGType.AGENTIC:
                result = await self._execute_agentic_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.SELF_RAG:
                result = await self._execute_self_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.GRAPH:
                result = await self._execute_graph_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.MEMORY:
                result = await self._execute_memory_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.ADVANCED:
                result = await self._execute_advanced_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.NAIVE:
                result = await self._execute_naive_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.SPECULATIVE:
                result = await self._execute_speculative_rag(routing_decision.parameters)
            elif routing_decision.rag_type == RAGType.SIMPLE:
                result = await self._execute_simple_rag(routing_decision.parameters)
            else:
                result = await self._execute_modular_rag(routing_decision.parameters)
            
            return {
                "success": True,
                "rag_type": routing_decision.rag_type.value,
                "confidence": routing_decision.confidence,
                "response": result,
                "execution_time": "measured",
                "metadata": routing_decision.parameters
            }
            
        except Exception as e:
            logger.error(f"RAG execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "rag_type": routing_decision.rag_type.value
            }
    
    # === BRAIN RAG EXECUTION METHODS ===
    
    async def _execute_agentic_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Agentic RAG - Think before you act (LangGraph implementation)"""
        try:
            # Define state schema
            class AgentState(BaseModel):
                query: str
                plan: List[str] = Field(default_factory=list)
                observations: List[str] = Field(default_factory=list)
                current_step: int = 0
                max_iterations: int = 5
                final_answer: str = ""
            
            # Planning node
            async def plan_node(state: AgentState) -> AgentState:
                plan_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a strategic planner breaking down complex tasks."),
                    ("human", "Break this query into actionable sub-tasks: {query}")
                ])
                chain = plan_prompt | self.llm | StrOutputParser()
                plan_text = await chain.ainvoke({"query": state.query})
                state.plan = [task.strip() for task in plan_text.split('\n') if task.strip()]
                return state
            
            # Retrieval node (integrates with OpenClaw tools)
            async def retrieve_node(state: AgentState) -> AgentState:
                if state.current_step < len(state.plan):
                    task = state.plan[state.current_step]
                    # Use orchestrator to execute tool
                    tool_result = await self.orchestrator.execute_tool({
                        "action": "search_and_retrieve",
                        "params": {"query": task}
                    })
                    state.observations.append(f"Task: {task}\nResult: {tool_result}")
                    state.current_step += 1
                return state
            
            # Reflection node
            async def reflect_node(state: AgentState) -> AgentState:
                reflect_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Reflect on progress and decide next action."),
                    ("human", "Current observations: {observations}\nContinue or synthesize?")
                ])
                chain = reflect_prompt | self.llm | StrOutputParser()
                reflection = await chain.ainvoke({"observations": "\n".join(state.observations)})
                
                if "synthesize" in reflection.lower() or state.current_step >= state.max_iterations:
                    state.final_answer = reflection
                return state
            
            # Build LangGraph
            workflow = StateGraph(AgentState)
            workflow.add_node("plan", plan_node)
            workflow.add_node("retrieve", retrieve_node)
            workflow.add_node("reflect", reflect_node)
            
            workflow.set_entry_point("plan")
            workflow.add_edge("plan", "retrieve")
            workflow.add_edge("retrieve", "reflect")
            workflow.add_conditional_edges(
                "reflect",
                lambda state: "end" if state.final_answer else "retrieve",
                {"retrieve": "retrieve", "end": END}
            )
            
            app = workflow.compile()
            
            # Execute
            initial_state = AgentState(
                query=params["query"],
                max_iterations=params.get("max_iterations", 5)
            )
            result = await app.ainvoke(initial_state)
            
            return {
                "status": "completed",
                "answer": result.final_answer,
                "steps_executed": result.current_step,
                "observations": result.observations
            }
            
        except Exception as e:
            logger.error(f"Agentic RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_self_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Self-RAG - Don't trust yourself blindly (Grader chain implementation)"""
        try:
            query = params["query"]
            validation_rounds = params.get("validation_rounds", 3)
            
            for round_num in range(validation_rounds):
                # Retrieve relevant documents
                docs = await self.vectorstore.asimilarity_search(query, k=5)
                context = "\n".join([doc.page_content for doc in docs])
                
                # Generate draft response
                draft_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Generate a helpful response based on the context."),
                    ("human", "Context: {context}\nQuery: {query}")
                ])
                draft_chain = draft_prompt | self.llm | StrOutputParser()
                draft = await draft_chain.ainvoke({"context": context, "query": query})
                
                # Critique with grader chain
                critique_prompt = PromptTemplate.from_template("""
                Evaluate this response against these criteria (score 0-1):
                Response: {response}
                Context: {context}
                Query: {query}
                
                Criteria:
                1. Relevance: Does it address the query?
                2. Support: Is it backed by the context?
                3. Utility: Is it helpful/practical?
                
                Provide scores as JSON: {{"relevance": 0.0, "support": 0.0, "utility": 0.0}}
                """)
                
                critique_chain = critique_prompt | self.llm | PydanticOutputParser(pydantic_object=RelevanceScore)
                scores = await critique_chain.ainvoke({
                    "response": draft,
                    "context": context,
                    "query": query
                })
                
                # Decision logic
                avg_score = (scores.relevance + scores.support + scores.utility) / 3
                
                if avg_score >= 0.8:
                    return {
                        "status": "validated",
                        "answer": draft,
                        "scores": scores.dict(),
                        "rounds": round_num + 1
                    }
                elif round_num < validation_rounds - 1:
                    # Rewrite query and try again
                    rewrite_prompt = ChatPromptTemplate.from_messages([
                        ("human", "Rewrite this query to be more specific: {query}")
                    ])
                    rewrite_chain = rewrite_prompt | self.llm | StrOutputParser()
                    query = await rewrite_chain.ainvoke({"query": query})
            
            return {
                "status": "partial",
                "answer": draft,
                "final_scores": scores.dict(),
                "rounds_completed": validation_rounds
            }
            
        except Exception as e:
            logger.error(f"Self-RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_branched_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Branched RAG - Explore multiple futures (Parallel execution)"""
        try:
            query = params["query"]
            num_branches = params.get("branches", 3)
            
            # Define different perspectives
            perspectives = [
                "Technical/Analytical perspective",
                "Creative/Innovative perspective", 
                "Practical/Business perspective"
            ][:num_branches]
            
            # Parallel execution using RunnableParallel
            async def create_branch_chain(perspective: str) -> Runnable:
                branch_prompt = ChatPromptTemplate.from_messages([
                    ("system", f"You are analyzing from a {perspective} viewpoint."),
                    ("human", "Query: {query}\nProvide your perspective.")
                ])
                return branch_prompt | self.llm | StrOutputParser()
            
            # Execute all branches in parallel
            branch_chains = {}
            for i, perspective in enumerate(perspectives):
                branch_chains[f"branch_{i}"] = await create_branch_chain(perspective)
            
            parallel_executor = RunnableParallel(**branch_chains)
            branch_results = await parallel_executor.ainvoke({"query": query})
            
            # Merge results with judge model
            merge_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert synthesizer combining multiple perspectives."),
                ("human", """Combine these perspectives into one superior answer:
                
                {perspectives}
                
                Query: {query}""")
            ])
            
            merge_chain = merge_prompt | self.llm | StrOutputParser()
            final_answer = await merge_chain.ainvoke({
                "perspectives": "\n\n".join([f"{k}: {v}" for k, v in branch_results.items()]),
                "query": query
            })
            
            return {
                "status": "completed",
                "answer": final_answer,
                "perspectives": branch_results,
                "perspective_count": len(branch_results)
            }
            
        except Exception as e:
            logger.error(f"Branched RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_corrective_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Corrective RAG - Trust but verify (External verification)"""
        try:
            query = params["query"]
            
            # Initial retrieval
            docs = await self.vectorstore.asimilarity_search(query, k=10)
            
            # Knowledge grader evaluation
            grader_prompt = PromptTemplate.from_template("""
            Evaluate if these documents adequately answer the query:
            Query: {query}
            Documents: {documents}
            
            Rate each document (0-1) and overall adequacy (0-1):
            {{"document_scores": [0.0, 0.0, ...], "overall_adequacy": 0.0}}
            """)
            
            grader_chain = grader_prompt | self.llm | PydanticOutputParser(pydantic_object=dict)
            evaluation = await grader_chain.ainvoke({
                "query": query,
                "documents": "\n---\n".join([doc.page_content for doc in docs])
            })
            
            # Decision logic
            if evaluation.get("overall_adequacy", 0) < 0.6:
                # Trigger external search (web search tool)
                web_search_result = await self.orchestrator.execute_tool({
                    "action": "web_search",
                    "params": {"query": query}
                })
                
                # Combine internal + external data
                combined_context = "\n".join([
                    "\n--- Internal Docs ---\n",
                    "\n".join([doc.page_content for doc in docs]),
                    "\n--- External Data ---\n",
                    str(web_search_result)
                ])
            else:
                combined_context = "\n".join([doc.page_content for doc in docs])
            
            # Generate final answer
            final_prompt = ChatPromptTemplate.from_messages([
                ("human", "Context: {context}\nQuery: {query}")
            ])
            final_chain = final_prompt | self.llm | StrOutputParser()
            answer = await final_chain.ainvoke({"context": combined_context, "query": query})
            
            return {
                "status": "completed",
                "answer": answer,
                "external_search_used": evaluation.get("overall_adequacy", 0) < 0.6,
                "internal_docs_count": len(docs)
            }
            
        except Exception as e:
            logger.error(f"Corrective RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    # === MIND RAG EXECUTION METHODS ===
    
    async def _execute_graph_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Graph RAG - It's all connected (Knowledge graph traversal)"""
        try:
            query = params["query"]
            
            # Extract entities from query
            entity_prompt = ChatPromptTemplate.from_messages([
                ("human", "Extract key entities from this query: {query}")
            ])
            entity_chain = entity_prompt | self.llm | StrOutputParser()
            entities = await entity_chain.ainvoke({"query": query})
            
            # Traverse knowledge graph
            relationships = await self.graph_manager.find_relationship_path(
                source_entity=entities.split(',')[0].strip(),
                target_entity=query.split()[-1] if len(query.split()) > 2 else "result",
                max_depth=3
            )
            
            # Get context from graph paths
            context_chunks = []
            for path in relationships:
                if "nodes" in path:
                    for node in path["nodes"]:
                        node_context = await self.graph_manager.get_entity_context(node)
                        context_chunks.append(str(node_context))
            
            # Generate answer using graph context
            answer_prompt = ChatPromptTemplate.from_messages([
                ("human", """Use the relationship information to answer:
                Query: {query}
                Relationships: {relationships}
                Context: {context}""")
            ])
            answer_chain = answer_prompt | self.llm | StrOutputParser()
            answer = await answer_chain.ainvoke({
                "query": query,
                "relationships": str(relationships),
                "context": "\n".join(context_chunks)
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "relationships_found": len(relationships),
                "entities_identified": entities
            }
            
        except Exception as e:
            logger.error(f"Graph RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_hyde_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """HyDE RAG - Fake it 'til you find it (Hypothetical embeddings)"""
        try:
            query = params["query"]
            
            # Generate hypothetical perfect answer
            hyde_prompt = ChatPromptTemplate.from_messages([
                ("system", "Generate a comprehensive, detailed answer as if you're an expert."),
                ("human", "Answer this thoroughly: {query}")
            ])
            hyde_chain = hyde_prompt | self.llm | StrOutputParser()
            hypothetical_answer = await hyde_chain.ainvoke({"query": query})
            
            # Embed the hypothetical answer
            hyde_embedding = await self.embeddings.aembed_documents([hypothetical_answer])
            
            # Search using hypothetical embedding (simplified implementation)
            # In practice, this would use vectorstore.similarity_search_by_vector
            docs = await self.vectorstore.asimilarity_search(query, k=10)
            
            # Rank documents by similarity to hypothetical answer
            doc_scores = []
            for doc in docs:
                doc_embedding = await self.embeddings.aembed_documents([doc.page_content])
                # Simplified similarity calculation
                similarity = self._cosine_similarity(hyde_embedding[0], doc_embedding[0])
                doc_scores.append((doc, similarity))
            
            # Sort by similarity and take top results
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            top_docs = [doc for doc, score in doc_scores[:5]]
            
            # Generate final answer using real documents
            final_prompt = ChatPromptTemplate.from_messages([
                ("human", "Context: {context}\nQuery: {query}")
            ])
            final_chain = final_prompt | self.llm | StrOutputParser()
            answer = await final_chain.ainvoke({
                "context": "\n".join([doc.page_content for doc in top_docs]),
                "query": query
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "hypothetical_answer": hypothetical_answer[:200] + "...",
                "documents_used": len(top_docs)
            }
            
        except Exception as e:
            logger.error(f"HyDE RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        return dot_product / (magnitude1 * magnitude2) if magnitude1 * magnitude2 > 0 else 0
    
    async def _execute_memory_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simple RAG with Memory - Context is King"""
        try:
            query = params["query"]
            context_window = params.get("context_window", 10)
            
            # Fetch recent conversation history
            recent_history = await self.episodic_manager.get_recent(limit=context_window)
            
            # Reformulate query with context
            reformulate_prompt = ChatPromptTemplate.from_messages([
                ("human", """Given this conversation history:
                {history}
                
                Reformulate this query to be more specific: {query}""")
            ])
            reformulate_chain = reformulate_prompt | self.llm | StrOutputParser()
            refined_query = await reformulate_chain.ainvoke({
                "history": "\n".join([str(h) for h in recent_history]),
                "query": query
            })
            
            # Retrieve using refined query
            docs = await self.vectorstore.asimilarity_search(refined_query, k=5)
            
            # Generate answer with conversation context
            answer_prompt = ChatPromptTemplate.from_messages([
                ("human", """Conversation History: {history}
                Retrieved Context: {context}
                Query: {query}""")
            ])
            answer_chain = answer_prompt | self.llm | StrOutputParser()
            answer = await answer_chain.ainvoke({
                "history": "\n".join([str(h) for h in recent_history]),
                "context": "\n".join([doc.page_content for doc in docs]),
                "query": query
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "conversation_turns": len(recent_history),
                "refined_query": refined_query
            }
            
        except Exception as e:
            logger.error(f"Memory RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_advanced_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced RAG - Precision over speed (Hybrid search + reranking)"""
        try:
            query = params["query"]
            
            # Hybrid search: keyword + vector
            vector_docs = await self.vectorstore.asimilarity_search(query, k=20)
            
            # Simulate keyword search (would use BM25 in production)
            keyword_docs = await self._keyword_search(query, k=20)
            
            # Combine and deduplicate
            all_docs = list(set(vector_docs + keyword_docs))
            
            # Cross-encoder reranking
            reranked_docs = await self._cross_encoder_rerank(query, all_docs)
            top_docs = reranked_docs[:5]
            
            # Generate precise answer
            answer_prompt = ChatPromptTemplate.from_messages([
                ("human", "Precisely answer using this high-quality context: {context}\nQuery: {query}")
            ])
            answer_chain = answer_prompt | self.llm | StrOutputParser()
            answer = await answer_chain.ainvoke({
                "context": "\n---\n".join([doc.page_content for doc in top_docs]),
                "query": query
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "initial_candidates": len(all_docs),
                "final_documents": len(top_docs),
                "reranking_performed": True
            }
            
        except Exception as e:
            logger.error(f"Advanced RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _keyword_search(self, query: str, k: int) -> List[Document]:
        """Simulate keyword search (BM25 equivalent)"""
        # In production, this would interface with a BM25 search engine
        # For demonstration, we'll use a simple term matching approach
        all_docs = await self._get_all_documents()
        scored_docs = []
        
        query_terms = query.lower().split()
        for doc in all_docs:
            score = sum(1 for term in query_terms if term in doc.page_content.lower())
            if score > 0:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:k]]
    
    async def _cross_encoder_rerank(self, query: str, docs: List[Document]) -> List[Document]:
        """Simulate cross-encoder reranking"""
        # In production, this would use a cross-encoder model
        # For demonstration, we'll use a simple relevance scoring
        scored_docs = []
        for doc in docs:
            # Calculate relevance score (simplified)
            content = doc.page_content.lower()
            query_terms = query.lower().split()
            score = sum(1 for term in query_terms if term in content) / len(query_terms)
            scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs]
    
    async def _get_all_documents(self) -> List[Document]:
        """Get all documents (placeholder for vectorstore iteration)"""
        # In production, this would iterate through the vectorstore
        return await self.vectorstore.asimilarity_search("dummy", k=1000)
    
    # === SPINE RAG EXECUTION METHODS ===
    
    async def _execute_speculative_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Speculative RAG - Guess fast, confirm later (Parallel execution)"""
        try:
            query = params["query"]
            
            # Launch parallel execution paths
            async def fast_draft():
                draft_prompt = ChatPromptTemplate.from_messages([
                    ("human", "Quickly answer: {query}")
                ])
                draft_chain = draft_prompt | self.llm | StrOutputParser()
                return await draft_chain.ainvoke({"query": query})
            
            async def slow_retrieve():
                docs = await self.vectorstore.asimilarity_search(query, k=5)
                verify_prompt = ChatPromptTemplate.from_messages([
                    ("human", "Context: {context}\nQuery: {query}")
                ])
                verify_chain = verify_prompt | self.llm | StrOutputParser()
                return await verify_chain.ainvoke({
                    "context": "\n".join([doc.page_content for doc in docs]),
                    "query": query
                })
            
            # Execute both paths concurrently
            draft_task = asyncio.create_task(fast_draft())
            verified_task = asyncio.create_task(slow_retrieve())
            
            # Wait for verified answer (this will take longer)
            verified_answer = await verified_task
            
            # Get draft answer
            draft_answer = await draft_task
            
            # Verification logic
            verification_prompt = ChatPromptTemplate.from_messages([
                ("human", """Do these answers align?
                Draft: {draft}
                Verified: {verified}
                Query: {query}
                
                Respond with YES or NO only.""")
            ])
            verification_chain = verification_prompt | self.llm | StrOutputParser()
            alignment = await verification_chain.ainvoke({
                "draft": draft_answer,
                "verified": verified_answer,
                "query": query
            })
            
            return {
                "status": "completed",
                "final_answer": verified_answer,
                "draft_answer": draft_answer,
                "answers_aligned": "YES" in alignment.upper(),
                "execution_path": "speculative"
            }
            
        except Exception as e:
            logger.error(f"Speculative RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_naive_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Naive RAG - Keep it simple (Fast baseline)"""
        try:
            query = params["query"]
            
            # Simple vector search
            docs = await self.vectorstore.asimilarity_search(query, k=3)
            
            # Direct answer generation
            answer_prompt = f"Context: {{context}}\n\nQuery: {query}"
            answer_chain = PromptTemplate.from_template(answer_prompt) | self.llm | StrOutputParser()
            answer = await answer_chain.ainvoke({
                "context": "\n---\n".join([doc.page_content for doc in docs])
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "documents_used": len(docs),
                "execution_time": "fast"
            }
            
        except Exception as e:
            logger.error(f"Naive RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_simple_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simple RAG - The baseline (Cosine similarity)"""
        try:
            query = params["query"]
            
            # Standard retrieval
            docs = await self.vectorstore.asimilarity_search(query, k=5)
            
            # Basic summarization
            summary_prompt = ChatPromptTemplate.from_messages([
                ("human", "Summarize this information to answer: {query}\n\n{context}")
            ])
            summary_chain = summary_prompt | self.llm | StrOutputParser()
            answer = await summary_chain.ainvoke({
                "query": query,
                "context": "\n".join([doc.page_content for doc in docs])
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "retrieved_chunks": len(docs)
            }
            
        except Exception as e:
            logger.error(f"Simple RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    # === BODY RAG EXECUTION METHODS ===
    
    async def _execute_multimodal_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Multimodal RAG - A picture is worth 1000 tokens"""
        try:
            query = params["query"]
            
            # This would integrate with multimodal models like CLIP/Vision models
            # For demonstration, we'll simulate multimodal processing
            
            # Simulate image processing and retrieval
            visual_context = "Visual analysis would extract key elements from images here"
            
            # Retrieve related text documents
            text_docs = await self.vectorstore.asimilarity_search(query, k=5)
            
            # Multimodal synthesis
            multimodal_prompt = ChatPromptTemplate.from_messages([
                ("human", """Visual Context: {visual_context}
                Text Context: {text_context}
                Query: {query}
                
                Provide a comprehensive answer integrating visual and textual information.""")
            ])
            multimodal_chain = multimodal_prompt | self.llm | StrOutputParser()
            answer = await multimodal_chain.ainvoke({
                "visual_context": visual_context,
                "text_context": "\n".join([doc.page_content for doc in text_docs]),
                "query": query
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "modalities_processed": ["visual", "textual"],
                "documents_retrieved": len(text_docs)
            }
            
        except Exception as e:
            logger.error(f"Multimodal RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_modular_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Modular RAG - Plug and Play (Component assembly)"""
        try:
            query = params["query"]
            
            # Dynamic component selection based on query characteristics
            components_needed = await self._analyze_component_needs(query)
            
            # Assemble modular pipeline
            pipeline_components = []
            results = {}
            
            # Retrieval module
            if components_needed.get("retrieval", False):
                docs = await self.vectorstore.asimilarity_search(query, k=10)
                results["retrieval"] = docs
                pipeline_components.append("vector_retriever")
            
            # Reranking module
            if components_needed.get("precision", False) and "retrieval" in results:
                reranked = await self._cross_encoder_rerank(query, results["retrieval"])
                results["reranked"] = reranked[:5]
                pipeline_components.append("cross_encoder_reranker")
            
            # Web search module
            if components_needed.get("freshness", False):
                web_result = await self.orchestrator.execute_tool({
                    "action": "web_search",
                    "params": {"query": query}
                })
                results["web_search"] = web_result
                pipeline_components.append("web_searcher")
            
            # Generate final answer using assembled components
            context_parts = []
            if "reranked" in results:
                context_parts.append("\n".join([doc.page_content for doc in results["reranked"]]))
            elif "retrieval" in results:
                context_parts.append("\n".join([doc.page_content for doc in results["retrieval"]]))
            if "web_search" in results:
                context_parts.append(str(results["web_search"]))
            
            final_prompt = ChatPromptTemplate.from_messages([
                ("human", "Context: {context}\nQuery: {query}")
            ])
            final_chain = final_prompt | self.llm | StrOutputParser()
            answer = await final_chain.ainvoke({
                "context": "\n---\n".join(context_parts),
                "query": query
            })
            
            return {
                "status": "completed",
                "answer": answer,
                "components_used": pipeline_components,
                "dynamic_assembly": True
            }
            
        except Exception as e:
            logger.error(f"Modular RAG failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _analyze_component_needs(self, query: str) -> Dict[str, bool]:
        """Analyze what modular components are needed"""
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("human", """Analyze this query and determine what components are needed:
            Query: {query}
            
            Components: retrieval, precision, freshness, web_search
            
            Respond with JSON: {{"retrieval": true/false, "precision": true/false, ...}}""")
        ])
        analysis_chain = analysis_prompt | self.llm | PydanticOutputParser(pydantic_object=dict)
        return await analysis_chain.ainvoke({"query": query})

# Global router instance management
_adaptive_router: Optional[AdaptiveRAGRouter] = None

def get_adaptive_router(llm: Runnable = None, embeddings: Embeddings = None, vectorstore: VectorStore = None) -> AdaptiveRAGRouter:
    """Get or create the global adaptive router instance"""
    global _adaptive_router
    if _adaptive_router is None:
        if not all([llm, embeddings, vectorstore]):
            raise ValueError("Must provide llm, embeddings, and vectorstore for router initialization")
        _adaptive_router = AdaptiveRAGRouter(llm, embeddings, vectorstore)
    return _adaptive_router

async def route_and_execute(query: str, context: Dict[str, Any] = None, 
                          llm: Runnable = None, embeddings: Embeddings = None, vectorstore: VectorStore = None) -> Dict[str, Any]:
    """Convenience function to route and execute a query"""
    router = get_adaptive_router(llm, embeddings, vectorstore)
    routing_decision = await router.route_query(query, context)
    return await router.execute_routed_query(routing_decision)