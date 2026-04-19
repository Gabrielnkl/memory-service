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
    memory_service = Depends(get_memory_service)
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
    memory_service = Depends(get_memory_service)
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
