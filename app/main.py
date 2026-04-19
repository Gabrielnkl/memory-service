# main.py - FastAPI Application Entry Point
#
# This is the main entry point for the Memory Service API.
# Now integrated with LangChain for advanced AI memory management.
#
# Responsibilities:
# - Create and configure the FastAPI application
# - Include API routes from routes.py
# - Set up LangChain components and configuration
# - Set up CORS, middleware, and other app-level configurations
# - Run the server when executed directly
#
# LangChain Integration:
# - Configure embedding providers (OpenAI, HuggingFace)
# - Set up vector stores (Chroma, Pinecone)
# - Initialize memory components
#
# What you need to implement:
# 1. Import FastAPI and create an app instance
# 2. Import and include the router from api/routes.py
# 3. Set up LangChain configuration (API keys, model selection)
# 4. Initialize LangChain components (embeddings, vector stores)
# 5. Add any necessary middleware (CORS, logging, etc.)
# 6. Add startup/shutdown event handlers for LangChain setup
# 7. Add a root endpoint (GET /) that returns service info
# 8. Add health check endpoint (GET /health)
# 9. Configure uvicorn to run the app when this file is executed

# TODO: Implement FastAPI app creation and configuration
# TODO: Include API routes
# TODO: Set up LangChain components and configuration
# TODO: Add middleware and event handlers
# TODO: Add root and health endpoints

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