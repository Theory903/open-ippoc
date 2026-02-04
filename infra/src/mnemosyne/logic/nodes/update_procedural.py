from mnemosyne.logic.state import MemoryState, ProceduralHint
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

class SkillInference(BaseModel):
    skill: Optional[str] = Field(description="A reusable skill, rule, or heuristic inferred from the fact. None if no clear skill.")
    trigger: Optional[str] = Field(description="The situation or trigger where this skill applies.")

def update_procedural(llm: Runnable):
    """
    Returns a node that infers procedural memory (skills) from facts.
    """
    parser = PydanticOutputParser(pydantic_object=SkillInference)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Hippocampus. Infer a reusable 'How-To' skill or rule from this fact if possible.\n{format_instructions}"),
        ("human", "{fact}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser

    async def _node(state: MemoryState) -> dict:
        hints = []
        
        for fact in state.extracted_facts:
            # Only learn from high confidence facts
            if fact.confidence > 0.7:
                try:
                    result = await chain.ainvoke({"fact": fact.fact})
                    
                    if result.skill:
                        hints.append(
                            ProceduralHint(
                                skill=result.skill,
                                trigger=result.trigger or fact.fact,
                                confidence=fact.confidence
                            )
                        )
                except Exception:
                    pass # Ignore inference failures
        
        return {"procedural_hints": hints}

    return _node
