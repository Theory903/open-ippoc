from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from ..semantic.rag import SemanticManager

class ProceduralManager:
    """
    Stores and Retrieves 'How-To' knowledge (Skills, Scripts, Workflows).
    Uses Semantic Memory but partitioned for 'skills'.
    """
    def __init__(self, semantic: SemanticManager):
        self.semantic = semantic
        self.collection_prefix = "skill_"

    async def register_skill(self, name: str, code: str, description: str, language: str = "python"):
        """
        Saves a skill definition.
        """
        content = f"SKILL: {name}\nLANG: {language}\nDESC: {description}\n\nCODE:\n{code}"
        metadata = {
            "type": "procedural",
            "skill_name": name,
            "language": language,
            "description": description
        }
        # In a real impl, we might store the code in a file/db and just vector index the description.
        # For now, we put it all in the vector store for retrieval.
        await self.semantic.index(content, metadata)
        return f"Skill '{name}' registered."

    async def find_skill(self, task_description: str) -> List[Dict[str, Any]]:
        """
        Finds code/tools relevant to a task.
        """
        # We append "How to" to bias towards procedural docs
        query = f"How to {task_description}"
        return await self.semantic.search(query, limit=3, min_score=0.75)
