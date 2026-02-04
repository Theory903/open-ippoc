from mnemosyne.logic.state import MemoryState, ExtractedFact
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

class FactExtraction(BaseModel):
    facts: List[str] = Field(description="List of atomic factual statements extracted from the text.")

def extract_facts(llm: Runnable):
    """
    Returns a graph node function that extracts facts from new events.
    """
    
    # 1. Define the extraction chain
    parser = PydanticOutputParser(pydantic_object=FactExtraction)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Hippocampus. extract atomic, timeless facts from the following event. Ignore hearsay. Focus on what is definitely true.\n{format_instructions}"),
        ("human", "{text}")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser

    async def _node(state: MemoryState) -> dict: # Returning dict to update state
        facts = []
        
        # Batch processing could be done here, for now linear
        for event in state.new_events:
            try:
                result = await chain.ainvoke({"text": event.content})
                
                for f in result.facts:
                    facts.append(
                        ExtractedFact(
                            fact=f,
                            embedding=None,  # Will be filled by index_vectors
                            confidence=event.confidence,
                            source_event_id=event.event_id,
                        )
                    )
            except Exception as e:
                # Fault tolerance: don't crash the brain, just log error to state
                # real implementation should use logger
                print(f"Error extracting facts: {e}")
                
        return {"extracted_facts": facts}

    return _node
