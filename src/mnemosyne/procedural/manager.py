from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from ..semantic.rag import SemanticManager, ContentType
import logging

logger = logging.getLogger(__name__)

class ProceduralManager:
    """
    Production-ready Procedural Memory Manager.
    
    Features:
    - Advanced skill registration with structured metadata
    - Multi-language code storage and retrieval
    - Semantic skill matching with confidence scoring
    - Context-aware skill recommendation
    - Skill versioning and dependency tracking
    """
    def __init__(self, semantic: SemanticManager):
        self.semantic = semantic
        self.collection_prefix = "skill_"
        self.skill_registry: Dict[str, Dict[str, Any]] = {}

    async def register_skill(self, name: str, code: str, description: str, 
                           language: str = "python", version: str = "1.0.0",
                           dependencies: List[str] = None, tags: List[str] = None) -> str:
        """
        Registers a skill with comprehensive metadata.
        
        Args:
            name: Unique skill identifier
            code: Implementation code
            description: Natural language description
            language: Programming language
            version: Skill version
            dependencies: Required dependencies
            tags: Skill categorization tags
            
        Returns:
            Registration confirmation message
        """
        try:
            # Create structured skill content
            skill_content = self._format_skill_content(name, code, description, language)
            
            # Build comprehensive metadata
            metadata = {
                "type": "procedural",
                "skill_name": name,
                "language": language,
                "version": version,
                "description": description,
                "dependencies": dependencies or [],
                "tags": tags or [],
                "registration_timestamp": "now",
                "usage_count": 0,
                "success_rate": 1.0
            }
            
            # Store in semantic memory with procedural content type
            object_ids = await self.semantic.add_memory(
                skill_content, 
                metadata, 
                ContentType.CODE
            )
            
            # Register in local registry
            self.skill_registry[name] = {
                "id": object_ids[0] if object_ids else None,
                "metadata": metadata,
                "content": skill_content
            }
            
            logger.info(f"Registered skill '{name}' (v{version}) with {len(object_ids)} objects")
            return f"Skill '{name}' registered successfully."
            
        except Exception as e:
            logger.error(f"Failed to register skill '{name}': {e}")
            raise

    async def find_skill(self, task_description: str, 
                       min_confidence: float = 0.8,
                       preferred_languages: List[str] = None) -> List[Dict[str, Any]]:
        """
        Finds relevant skills for a task using advanced semantic matching.
        
        Args:
            task_description: Description of desired functionality
            min_confidence: Minimum confidence threshold
            preferred_languages: Preferred programming languages
            
        Returns:
            List of matching skills with metadata
        """
        try:
            # Enhance query for procedural matching
            enhanced_query = f"How to {task_description} implementation code"
            
            # Retrieve relevant documents
            documents = await self.semantic.retrieve_relevant(
                enhanced_query,
                k=10,
                min_score=min_confidence,
                use_advanced_retrieval=True
            )
            
            # Filter and format results
            skills = []
            for doc in documents:
                if doc.metadata.get("type") == "procedural":
                    skill_data = self._extract_skill_data(doc)
                    
                    # Apply language filter if specified
                    if preferred_languages and skill_data["language"] not in preferred_languages:
                        continue
                    
                    skills.append(skill_data)
            
            # Sort by confidence and recency
            skills.sort(key=lambda x: (
                x.get("confidence", 0),
                x.get("metadata", {}).get("success_rate", 0)
            ), reverse=True)
            
            logger.debug(f"Found {len(skills)} relevant skills for: {task_description}")
            return skills[:5]  # Return top 5 matches
            
        except Exception as e:
            logger.error(f"Skill search failed for '{task_description}': {e}")
            return []

    async def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific skill by name"""
        return self.skill_registry.get(name)

    async def list_skills(self, language: str = None, tag: str = None) -> List[Dict[str, Any]]:
        """List all registered skills with optional filtering"""
        skills = []
        
        for name, skill_data in self.skill_registry.items():
            metadata = skill_data.get("metadata", {})
            
            # Apply filters
            if language and metadata.get("language") != language:
                continue
            if tag and tag not in metadata.get("tags", []):
                continue
                
            skills.append({
                "name": name,
                "language": metadata.get("language"),
                "version": metadata.get("version"),
                "description": metadata.get("description"),
                "tags": metadata.get("tags", []),
                "dependencies": metadata.get("dependencies", [])
            })
        
        return skills

    def _format_skill_content(self, name: str, code: str, description: str, language: str) -> str:
        """Format skill content for storage"""
        return f"""
SKILL: {name}
LANGUAGE: {language}
DESCRIPTION: {description}

IMPLEMENTATION:
{code}
        """.strip()

    def _extract_skill_data(self, document: Document) -> Dict[str, Any]:
        """Extract structured skill data from document"""
        metadata = document.metadata
        
        return {
            "name": metadata.get("skill_name", "unknown"),
            "language": metadata.get("language", "unknown"),
            "version": metadata.get("version", "1.0.0"),
            "description": metadata.get("description", ""),
            "content": document.page_content,
            "confidence": metadata.get("confidence", 0.0),
            "metadata": metadata,
            "object_id": metadata.get("object_id")
        }

    async def unregister_skill(self, name: str) -> bool:
        """
        Unregister a skill by name.

        Args:
            name: Skill identifier

        Returns:
            Success status
        """
        try:
            if name not in self.skill_registry:
                logger.warning(f"Attempted to unregister unknown skill: {name}")
                return False

            skill_data = self.skill_registry.pop(name)

            # Remove from semantic memory if object ID is available
            object_id = skill_data.get("id")
            if object_id:
                await self.semantic.delete_memories([object_id])

            logger.info(f"Unregistered skill: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister skill '{name}': {e}")
            return False
