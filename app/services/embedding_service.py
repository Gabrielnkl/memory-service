# embedding_service.py - Text Embedding Generation with LangChain
#
# This service handles converting text into vector embeddings using LangChain.
# LangChain provides unified interfaces to various embedding providers:
# - OpenAI embeddings (high quality, requires API key)
# - HuggingFace embeddings (free, local models)
# - Cohere, Google, etc.
#
# What you need to implement:
# 1. Import LangChain embedding classes
# 2. Create EmbeddingService class
# 3. Choose an embedding provider (start with OpenAIEmbeddings or HuggingFaceEmbeddings)
# 4. Implement generate_embedding(text: str) -> List[float] method:
#    - Use LangChain's embed_query() method
# 5. Implement generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
#    - Use LangChain's embed_documents() method
# 6. Add configuration for API keys and model selection
# 7. Handle rate limits and errors
#
# LangChain advantage: Easy switching between embedding providers!

# TODO: Import LangChain embeddings (OpenAIEmbeddings, HuggingFaceEmbeddings)
# TODO: Create EmbeddingService class with LangChain integration
# TODO: Implement generate_embedding using LangChain
# TODO: Implement batch embedding generation
# TODO: Add configuration management

from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

class EmbeddingService:
    def __init__(self):
        # Initialize embedding provider (start with OpenAIEmbeddings or HuggingFaceEmbeddings)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.embedding_model = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=openai_api_key
            )
        else:
            # Fallback to free HuggingFace embeddings
            self.embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embedding_model.embed_query(text)

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return self.embedding_model.embed_documents(texts)
