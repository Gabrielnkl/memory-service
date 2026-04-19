import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import os

from app.api.routes import router
from app.services.memory_service import MemoryService

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔥 STARTUP RUNNING")

    # initialize service
    app.state.memory_service = MemoryService()
    await app.state.memory_service.postgres.connect()

    yield

    print("🛑 SHUTDOWN RUNNING")
    await app.state.memory_service.postgres.close()


app = FastAPI(lifespan=lifespan)

# routes
app.include_router(router)

# CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Memory Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
