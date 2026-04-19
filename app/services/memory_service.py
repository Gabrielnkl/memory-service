# memory_service.py - Core Memory Service Logic with LangChain
#
# This orchestrates memory operations using LangChain's unified interfaces.
# LangChain provides high-level memory abstractions that combine multiple storage backends.
#
# Memory Flow with LangChain:
# When storing a message:
# 1. Store full message in Postgres (long-term storage)
# 2. Store recent messages in Redis (short-term cache)
# 3. Use LangChain's embedding service to generate embeddings
# 4. Store in LangChain's vector store (Chroma, Pinecone, etc.)
#
# When recalling memory:
# 1. Get recent messages from Redis
# 2. Use LangChain's vector store similarity search
# 3. Combine and return as context
#
# LangChain Advantages:
# - Unified API across different storage backends
# - Built-in memory management patterns
# - Easy to extend with new providers
# - Production-ready implementations
#
# What you need to implement:
# 1. Import LangChain components and your custom services
# 2. Create MemoryService class
# 3. Implement store_message(user_id: str, text: str) method:
#    - Store in Postgres
#    - Update Redis cache
#    - Generate embedding with LangChain
#    - Store in LangChain vector store
# 4. Implement recall_memory(user_id: str) method:
#    - Get recent messages from Redis
#    - Use LangChain vector store similarity search
#    - Merge and return combined context
# 5. Implement search_memory(query: str, user_id: Optional[str]) method:
#    - Use LangChain for query embedding and search
#    - Return relevant memories
# 6. Add error handling and logging
#
# Consider using LangChain's built-in memory classes for inspiration!

# TODO: Import LangChain components and your database services
# TODO: Create MemoryService class with LangChain integration
# TODO: Implement store_message method using LangChain embeddings
# TODO: Implement recall_memory method with LangChain vector search
# TODO: Implement search_memory method
# TODO: Add proper error handling

import logging
from typing import List, Optional, Dict, Any

from app.db.postgres import PostgresService
from app.db.vector_db import VectorDBService


class MemoryService:
    def __init__(self):
        self.postgres = PostgresService()
        self.vector_db = VectorDBService()
        self.logger = logging.getLogger("MemoryService")

    # ------------------------------------------------------------------
    # Store message
    # ------------------------------------------------------------------
    async def store_message(self, user_id: str, text: str) -> str:
        try:
            # 1. Store in Postgres
            message_id = await self.postgres.store_message(user_id, text)

            # 2. Store in Vector DB (embedding handled automatically)
            self.vector_db.store_embedding(user_id, text, message_id)

            return message_id

        except Exception as e:
            self.logger.error(f"Error storing message: {e}")
            raise

    # ------------------------------------------------------------------
    # Recall memory (recent + semantic)
    # ------------------------------------------------------------------
    async def recall_memory(self, user_id: str) -> Dict[str, Any]:
        try:
            # 1. Get recent messages
            recent_messages = await self.postgres.get_user_messages(user_id, limit=5)

            # 2. Use last message as query (if exists)
            similar_memories = []
            if recent_messages:
                last_text = recent_messages[-1].get("text", "")

                if last_text:
                    similar_memories = self.vector_db.search_similar(
                        user_id=user_id,
                        query=last_text,
                        limit=3
                    )

            return {
                "user_id": user_id,
                "recent_messages": recent_messages,
                "similar_memories": similar_memories,
                "context": self._build_context(recent_messages, similar_memories)
            }

        except Exception as e:
            self.logger.error(f"Error recalling memory: {e}")
            raise

    # ------------------------------------------------------------------
    # Search memory
    # ------------------------------------------------------------------
    async def search_memory(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ):
        try:
            results = self.vector_db.search_similar(
                user_id=user_id or "",
                query=query,
                limit=limit
            )

            return results

        except Exception as e:
            self.logger.error(f"Error searching memory: {e}")
            raise

    # ------------------------------------------------------------------
    # Build context
    # ------------------------------------------------------------------
    def _build_context(
        self,
        recent_messages: List[Dict],
        similar_memories: List[Dict]
    ) -> str:
        context_parts = []

        if recent_messages:
            context_parts.append("Recent messages:")
            for msg in recent_messages[-3:]:
                context_parts.append(f"- {msg.get('text', '')}")

        if similar_memories:
            context_parts.append("\nRelevant memories:")
            for memory in similar_memories[:2]:
                context_parts.append(f"- {memory.get('text', '')}")

        return "\n".join(context_parts)