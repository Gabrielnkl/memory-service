# routes.py - API Endpoints for Memory Service
#
# This file defines all the REST API endpoints for the memory service.
# Now powered by LangChain for advanced AI memory capabilities.
#
# The memory service provides three main operations:
# 1. Store messages (POST /store) - Uses LangChain embeddings
# 2. Recall memory for a user (GET /recall/{user_id}) - LangChain vector search
# 3. Search semantic memory (GET /search) - LangChain similarity search
#
# LangChain Integration:
# - Embeddings: Unified interface to OpenAI, HuggingFace, etc.
# - Vector Stores: Chroma, Pinecone, Weaviate, etc.
# - Memory: Built-in patterns for conversation memory
#
# What you need to implement:
# 1. Create an APIRouter instance
# 2. Define POST /store endpoint:
#    - Accept JSON with user_id and text
#    - Validate input using Pydantic models from schemas.py
#    - Call memory_service.store_message() (now with LangChain)
#    - Return success response
# 3. Define GET /recall/{user_id} endpoint:
#    - Get user_id from path parameter
#    - Call memory_service.recall_memory() (LangChain-powered)
#    - Return combined short-term + semantic memory
# 4. Define GET /search endpoint:
#    - Accept query parameter 'q' for search text
#    - Optional user_id parameter
#    - Call memory_service.search_memory() (LangChain similarity search)
#    - Return relevant memories
# 5. Add proper error handling and status codes
# 6. Add response models using schemas.py
#
# LangChain advantage: Your API becomes an AI-ready memory system!

# TODO: Import necessary modules (FastAPI, schemas, memory_service)
# TODO: Create APIRouter instance
# TODO: Implement POST /store endpoint with LangChain integration
# TODO: Implement GET /recall/{user_id} endpoint
# TODO: Implement GET /search endpoint
# TODO: Add error handling and validation

from fastapi import APIRouter, HTTPException, Depends, Request
from app.models.schemas import MessageStoreRequest

router = APIRouter()

def get_memory_service(request: Request):
    return request.app.state.memory_service


@router.post("/store")
async def store_message(
    request: MessageStoreRequest,
    memory_service = Depends(get_memory_service)
):
    try:
        message_id = await memory_service.store_message(
            request.user_id,
            request.text
        )

        return {
            "message": "Message stored successfully",
            "message_id": message_id,
            "user_id": request.user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recall/{user_id}")
async def recall_memory(
    user_id: str,
    memory_service = Depends(get_memory_service)  # ✅ FIX
):
    try:
        return await memory_service.recall_memory(user_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_memory(
    q: str,
    user_id: str = None,
    limit: int = 5,
    memory_service = Depends(get_memory_service)  # ✅ FIX
):
    try:
        results = await memory_service.search_memory(q, user_id, limit)

        return {
            "query": q,
            "user_id": user_id,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))