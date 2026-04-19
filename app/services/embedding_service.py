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
