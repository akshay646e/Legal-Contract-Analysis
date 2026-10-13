import os
import math
from typing import List, Dict, Any, Optional
from app.config import settings
from app.core.logging import logger
from app.rag.chunker import LegalChunk

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available; falling back to memory vector store.")

class VectorStoreManager:
    """
    Manages vector storage and indexing for legal contract chunks.
    Supports ChromaDB persistence with an in-memory cosine fallback.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        self.client = None
        self.collection = None
        self._memory_chunks: Dict[str, List[LegalChunk]] = {} # fallback: contract_id -> list of chunks

        if CHROMA_AVAILABLE:
            try:
                os.makedirs(self.persist_dir, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_dir)
                self.collection = self.client.get_or_create_collection(
                    name="legal_contracts_v1",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Initialized ChromaDB at: [green]{self.persist_dir}[/green]")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB ({e}). Using memory vector fallback.")
                self.client = None

    def add_chunks(self, contract_id: str, chunks: List[LegalChunk], embeddings: Optional[List[List[float]]] = None) -> bool:
        """Stores contract chunks with metadata."""
        if not chunks:
            return True

        # Always keep in memory fallback for resilience
        self._memory_chunks[contract_id] = chunks

        if self.collection:
            try:
                ids = [c.chunk_id for c in chunks]
                documents = [c.text for c in chunks]
                metadatas = []
                for c in chunks:
                    meta = {
                        "contract_id": contract_id,
                        "section_number": c.section_number or "",
                        "section_title": c.section_title or "",
                        "page_number": c.page_number,
                        "chunk_index": c.chunk_index
                    }
                    metadatas.append(meta)

                if embeddings and len(embeddings) == len(chunks):
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        embeddings=embeddings,
                        metadatas=metadatas
                    )
                else:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                logger.info(f"Indexed [cyan]{len(chunks)}[/cyan] chunks for contract [yellow]{contract_id}[/yellow] into ChromaDB")
                return True
            except Exception as e:
                logger.error(f"Error adding chunks to ChromaDB: {e}. Stored in fallback store.")
                return True

        return True

    def similarity_search(
        self,
        contract_id: str,
        query: str,
        k: int = 4,
        query_embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant chunks for a specific contract.
        Scoped to contract_id to prevent cross-document contamination.
        """
        results = []

        if self.collection:
            try:
                where_filter = {"contract_id": contract_id}
                if query_embedding:
                    query_res = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(k, 10),
                        where=where_filter
                    )
                else:
                    query_res = self.collection.query(
                        query_texts=[query],
                        n_results=min(k, 10),
                        where=where_filter
                    )

                if query_res and "documents" in query_res and query_res["documents"]:
                    docs = query_res["documents"][0]
                    metas = query_res["metadatas"][0] if "metadatas" in query_res else [{}] * len(docs)
                    distances = query_res["distances"][0] if "distances" in query_res and query_res["distances"] else [0.0] * len(docs)

                    for doc, meta, dist in zip(docs, metas, distances):
                        results.append({
                            "text": doc,
                            "section_number": meta.get("section_number", ""),
                            "section_title": meta.get("section_title", ""),
                            "page_number": meta.get("page_number", 1),
                            "chunk_index": meta.get("chunk_index", 0),
                            "score": 1.0 - float(dist) if dist is not None else 0.85
                        })
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"ChromaDB search query failed ({e}); falling back to lexical search.")

        # In-memory keyword/lexical similarity search fallback
        contract_chunks = self._memory_chunks.get(contract_id, [])
        if not contract_chunks:
            return []

        scored_chunks = []
        query_words = set(query.lower().split())

        for c in contract_chunks:
            chunk_words = c.text.lower().split()
            # Simple term overlap score
            overlap = sum(1 for w in query_words if w in chunk_words)
            if overlap > 0:
                scored_chunks.append((overlap, c))

        # Sort by highest term overlap
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:k] if scored_chunks else [(0, c) for c in contract_chunks[:k]]

        for score, chunk in top_chunks:
            results.append({
                "text": chunk.text,
                "section_number": chunk.section_number or "",
                "section_title": chunk.section_title or "",
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "score": 0.85 + (score * 0.02)
            })

        return results

    def delete_contract(self, contract_id: str) -> bool:
        """Removes all chunks associated with a contract."""
        if self.collection:
            try:
                self.collection.delete(where={"contract_id": contract_id})
            except Exception as e:
                logger.warning(f"Error removing chunks from ChromaDB: {e}")

        if contract_id in self._memory_chunks:
            del self._memory_chunks[contract_id]

        return True

# Global vector store manager singleton
vector_store = VectorStoreManager()
