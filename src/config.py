import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    LLM_MODEL = "qwen-plus"
    TEMPERATURE = 0.7

    CHROMA_DB_PATH = "vector_db"
    EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
