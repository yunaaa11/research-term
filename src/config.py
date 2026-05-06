import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Model Settings
    LLM_MODEL = "qwen-plus"  # 也可以改成 gpt-4o 等
    TEMPERATURE = 0.7
    
    # RAG Settings
    CHROMA_DB_PATH = "vector_db"
    EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"