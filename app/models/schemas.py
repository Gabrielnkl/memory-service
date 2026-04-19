# schemas.py - Pydantic Models for API Validation
#
# These models work seamlessly with LangChain's data structures.
# LangChain uses similar patterns for Documents, Messages, and Memory objects.
#
# Key integration points:
# - MessageStoreRequest → LangChain Document creation
# - MessageResponse → LangChain message format
# - MemoryRecallResponse → LangChain memory retrieval
#
# What you need to implement:
# 1. Import Pydantic BaseModel
# 2. Define MessageStoreRequest model:
#    - user_id: str (required)
#    - text: str (required, min_length, max_length)
#    - Maps to LangChain Document(page_content=text, metadata={"user_id": user_id})
# 3. Define MessageResponse model:
#    - id: str
#    - user_id: str
#    - text: str
#    - timestamp: datetime
#    - Compatible with LangChain message formats
# 4. Define MemoryRecallResponse model:
#    - user_id: str
#    - recent_messages: List[MessageResponse] (from Redis)
#    - similar_memories: List[MessageResponse] (from LangChain vector search)
#    - context: str (combined context for LLM)
# 5. Define SearchRequest model:
#    - query: str (required)
#    - user_id: Optional[str]
#    - limit: Optional[int] = 10
# 6. Define SearchResponse model:
#    - query: str
#    - results: List[MessageResponse] (from LangChain similarity search)
# 7. Define ErrorResponse model for error handling
# 8. Add validation rules (min/max lengths, patterns, etc.)
#
# LangChain advantage: Your API models will integrate naturally with LangChain's memory systems!

# TODO: Import Pydantic BaseModel and field types
# TODO: Define request models (MessageStoreRequest, SearchRequest)
# TODO: Define response models (MessageResponse, MemoryRecallResponse, SearchResponse)
# TODO: Define error models
# TODO: Add validation rules and constraints

import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class MessageStoreRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=5000)

class MessageResponse(BaseModel):
    id: str
    user_id: str
    text: str
    timestamp: datetime.datetime

class MemoryRecallResponse(BaseModel):
    user_id: str
    recent_messages: List[MessageResponse]
    similar_memories: List[MessageResponse]
    context: str

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    user_id: Optional[str] = None
    limit: Optional[int] = Field(default=10, ge=1, le=50)

class SearchResponse(BaseModel):
    query: str
    results: List[MessageResponse]

class ErrorResponse(BaseModel):
    detail: str

