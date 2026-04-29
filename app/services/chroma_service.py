"""
ChromaDB service for RAG chatbot — embeds comments and supports similarity search.
"""

import os
import logging

import chromadb

logger = logging.getLogger(__name__)


class ChromaService:
    """Manages ChromaDB collections for per-analysis comment embeddings."""

    _instance = None

    def __init__(self):
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"ChromaDB initialized at {persist_dir}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _collection_name(self, analysis_id):
        return f"analysis_{analysis_id}"

    def embed_comments(self, analysis_id, comments_data, batch_size=500):
        """
        Embed comments into a ChromaDB collection.

        Args:
            analysis_id: Analysis UUID
            comments_data: List of dicts with keys:
                - id, preprocessed_text, original_text, model_sentiment, model_confidence
        """
        collection = self.client.get_or_create_collection(
            name=self._collection_name(analysis_id),
            metadata={"hnsw:space": "cosine"},
        )

        for i in range(0, len(comments_data), batch_size):
            batch = comments_data[i : i + batch_size]
            ids = [item["id"] for item in batch]
            documents = [item["preprocessed_text"] for item in batch]
            metadatas = [
                {
                    "original_text": item["original_text"][:500],
                    "sentiment": item["model_sentiment"],
                    "confidence": item["model_confidence"],
                }
                for item in batch
            ]
            collection.add(ids=ids, documents=documents, metadatas=metadatas)

        logger.info(f"Embedded {len(comments_data)} comments for analysis {analysis_id}")

    def query(self, analysis_id, question, top_k=10):
        """Query ChromaDB for comments similar to the question."""
        try:
            collection = self.client.get_collection(name=self._collection_name(analysis_id))
        except Exception:
            return []

        results = collection.query(query_texts=[question], n_results=top_k)
        sources = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                sources.append({
                    "document": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
        return sources

    def delete_collection(self, analysis_id):
        """Delete a ChromaDB collection for a given analysis."""
        try:
            self.client.delete_collection(name=self._collection_name(analysis_id))
        except Exception as e:
            logger.warning(f"Could not delete ChromaDB collection: {e}")
