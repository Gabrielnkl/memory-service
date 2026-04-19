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

