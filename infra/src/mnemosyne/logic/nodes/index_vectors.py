from mnemosyne.logic.state import MemoryState
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

def index_vectors(vector_store: VectorStore, embeddings: Embeddings):
    """
    Returns a node that embeds facts and stores them in the Vector DB.
    """
    async def _node(state: MemoryState) -> dict:
        
        # 1. Embed facts that don't have embeddings yet
        texts_to_embed = [f.fact for f in state.extracted_facts if f.embedding is None]
        
        if texts_to_embed:
            vectors = await embeddings.aembed_documents(texts_to_embed)
            
            # Map back to facts
            idx = 0
            for f in state.extracted_facts:
                if f.embedding is None:
                    f.embedding = vectors[idx]
                    idx += 1
        
        # 2. Add to VectorStore
        # We assume vector_store supports standard add_texts or add_documents
        # For PGVector, we usually use add_texts with metadata
        
        texts = []
        metadatas = []
        vectors = []
        
        for f in state.extracted_facts:
            texts.append(f.fact)
            metadatas.append({
                "source": f.source_event_id,
                "confidence": f.confidence,
                "created_at": f.created_at
            })
            vectors.append(f.embedding)
            
        if texts:
            # Note: Many vector stores don't support explicit vector insertion easily via standard API
            # Ideally we use add_embeddings if available, or just re-embed via the store if needed.
            # However, for efficiency, if we computed embeddings, we should use them.
            # Standard LangChain VectorStore interface is `add_texts` (computes embeddings) or specific methods.
            
            # Use `add_texts` which will re-embed locally (inefficient but standard)
            # OR pass the embeddings if the specific store allows.
            # For now, we utilize the store's add_texts which guarantees consistency. 
            # We computed embeddings above just to enrich the in-memory state for immediate procedural use.
            
            await vector_store.aadd_texts(texts=texts, metadatas=metadatas)
            
        return {"extracted_facts": state.extracted_facts} # No change to list, just side effect

    return _node
