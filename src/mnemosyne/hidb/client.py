import os
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# Third-party imports
try:
    import redis
except ImportError:
    redis = None

try:
    from langchain_community.vectorstores import PGVector
    from langchain_core.documents import Document
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError:
    PGVector = None
    Document = None
    GoogleGenerativeAIEmbeddings = None

logger = logging.getLogger(__name__)

@dataclass
class Record:
    """Standard record format for HiDB"""
    content: str
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None
    id: Optional[str] = None
    score: Optional[float] = None

class HiDB:
    """
    The Cognitive Substrate (Vector Database).
    Abstracts PostgreSQL/pgvector and Redis into a single Memory interface.
    """

    def __init__(self, db_url: str = None, redis_url: str = None, embeddings = None):
        """
        Initialize HiDB with database connections.

        Args:
            db_url: PostgreSQL connection string
            redis_url: Redis connection string
            embeddings: Embedding model instance
        """
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+psycopg2://ippoc:ippoc@localhost:5432/ippoc")
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Initialize Redis
        self.redis_client = None
        if redis:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                logger.info("HiDB: Redis connection initialized")
            except Exception as e:
                logger.warning(f"HiDB: Failed to connect to Redis: {e}")
        else:
            logger.warning("HiDB: Redis package not installed")

        # Initialize Vector Store
        self.embeddings = embeddings
        self.vector_store = None

        if not self.embeddings and GoogleGenerativeAIEmbeddings:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                try:
                    self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
                except Exception as e:
                    logger.warning(f"HiDB: Failed to initialize default embeddings: {e}")

        if PGVector and self.embeddings:
            try:
                # PGVector from langchain_community
                self.vector_store = PGVector(
                    connection_string=self.db_url,
                    embedding_function=self.embeddings,
                    collection_name="hippocampus_v2",
                )
                logger.info("HiDB: PGVector initialized")
            except Exception as e:
                logger.error(f"HiDB: Failed to initialize PGVector: {e}")
        else:
            if not PGVector:
                logger.warning("HiDB: langchain_community.vectorstores.PGVector not available")
            if not self.embeddings:
                logger.warning("HiDB: No embeddings model provided or available")

    def semantic_search(self, vector: List[float], k: int = 5) -> List[Record]:
        """
        Search for records semantically similar to the query vector.

        Args:
            vector: Query embedding vector
            k: Number of results to return

        Returns:
            List of Record objects
        """
        if not self.vector_store:
            logger.warning("HiDB: Vector store not initialized, returning empty results")
            return []

        try:
            results = self.vector_store.similarity_search_by_vector_with_score(vector, k=k)

            records = []
            for doc, score in results:
                records.append(Record(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    vector=None, # Usually not returned by similarity_search
                    id=doc.metadata.get("object_id") or doc.metadata.get("id"),
                    score=score
                ))
            return records

        except Exception as e:
            logger.error(f"HiDB: Semantic search failed: {e}")
            return []

    def insert_memory(self, record: Union[Record, Dict[str, Any]]) -> Optional[str]:
        """
        Insert a memory record into the database.

        Args:
            record: Record object or dictionary with content and metadata

        Returns:
            ID of the inserted record, or None if failed
        """
        if not self.vector_store:
            logger.warning("HiDB: Vector store not initialized, cannot insert memory")
            return None

        try:
            # Normalize input
            if isinstance(record, dict):
                content = record.get("content", "")
                metadata = record.get("metadata", {})
                rec_id = record.get("id")
            else:
                content = record.content
                metadata = record.metadata
                rec_id = record.id

            # Create Document
            doc = Document(
                page_content=content,
                metadata=metadata
            )

            # Add to vector store
            ids = self.vector_store.add_documents([doc], ids=[rec_id] if rec_id else None)

            if ids:
                inserted_id = ids[0]

                # Optionally store in Redis if configured
                if self.redis_client:
                    try:
                        import json
                        self.redis_client.set(
                            f"memory:{inserted_id}",
                            json.dumps({"content": content, "metadata": metadata})
                        )
                    except Exception as re:
                        logger.warning(f"HiDB: Failed to cache in Redis: {re}")

                return inserted_id
            return None

        except Exception as e:
            logger.error(f"HiDB: Insert memory failed: {e}")
            return None
