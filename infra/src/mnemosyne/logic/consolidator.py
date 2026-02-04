from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from ..episodic.manager import EpisodicManager, EpisodicEvent
from ..semantic.rag import SemanticManager

class MemoryConsolidator:
    def __init__(self, episodic: EpisodicManager, semantic: SemanticManager):
        self.episodic = episodic
        self.semantic = semantic
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0) # High reasoning for consolidation

    async def consolidate_recent(self, hours: int = 24):
        """
        Reads recent episodic events, summarizes them into 'Facts' and 'Rules',
        and stores them in Semantic Memory.
        This fits the 'Sleep' or 'Reflection' cycle.
        """
        # 1. Fetch raw events (Mocking fetch by time for now)
        # In real impl, we'd query `episodic.get_unconsolidated(hours)`
        # For now, we search generally to simulate
        events = await self.episodic.search(limit=50) # Get last 50 actions
        
        if not events:
            return "No recent events to consolidate."

        event_text = "\n".join([f"[{e['metadata'].get('timestamp')}] {e['content']}" for e in events])

        # 2. Reflection / Extraction
        # We ask the LLM to extract "Enduring Knowledge" vs "Transient Noise"
        prompt = ChatPromptTemplate.from_template("""
        You are the Hippocampus of an AI Agent.
        Review the following episodic log of recent actions:
        
        {log}
        
        Identify:
        1. Valid Facts learned (e.g., "User prefers Python", "File X is located at Y")
        2. Generalizable Rules (e.g., "Always use tool Z for task A")
        
        Output only the extracted knowledge points, one per line.
        Ignore transient errors or chatter.
        """)

        chain = prompt | self.llm
        result = await chain.ainvoke({"log": event_text})
        knowledge_points = result.content.strip().split("\n")

        # 3. Storage (Harden into Semantic Memory)
        count = 0
        for point in knowledge_points:
            if point.strip():
                # We tag this as "consolidated_knowledge"
                await self.semantic.index(
                    content=point.strip(), 
                    metadata={"source": "self_reflection", "origin": "episodic_consolidation"}
                )
                count += 1
                
        return f"Consolidated {count} new knowledge points from recent history."
