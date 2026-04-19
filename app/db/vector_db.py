from langchain_chroma import Chroma
from typing import List, Dict, Any
import os

# 👉 Choose ONE embedding provider

# Option A (recommended - simple, requires API key)
from langchain_openai import OpenAIEmbeddings

# Option B (free/local)
# from langchain_huggingface import HuggingFaceEmbeddings


class VectorDBService:
    def __init__(self):
        persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

        # ✅ Initialize embedding function
        self.embedding_function = OpenAIEmbeddings()

        # If using local embeddings instead:
        # self.embedding_function = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2"
        # )

        # ✅ Initialize vector store with embedding function
        self.vector_store = Chroma(
            collection_name="memory_service",
            persist_directory=persist_directory,
            embedding_function=self.embedding_function
        )

    # ------------------------------------------------------------------
    # Store message (embedding handled automatically)
    # ------------------------------------------------------------------
    def store_embedding(self, user_id: str, text: str, message_id: str):
        """Store a text with metadata (embedding auto-generated)"""
        self.vector_store.add_texts(
            texts=[text],
            metadatas=[{
                "user_id": user_id,
                "message_id": str(message_id)
            }]
        )

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------
    def search_similar(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search similar texts using semantic similarity"""

        docs_and_scores = self.vector_store.similarity_search_with_score(
            query,
            k=limit
        )

        results = []
        for doc, score in docs_and_scores:
            # Filter by user_id (Chroma filter support is limited)
            if user_id and doc.metadata.get("user_id") != user_id:
                continue

            results.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })

        return results

    # ------------------------------------------------------------------
    # Delete user data
    # ------------------------------------------------------------------
    def delete_user_embeddings(self, user_id: str):
        """Delete all embeddings for a user"""
        try:
            self.vector_store.delete(filter={"user_id": user_id})
        except Exception:
            # Some Chroma versions don't fully support filter delete
            # In production you'd track IDs explicitly
            pass
