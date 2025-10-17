import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    google_api_key: str = ""
    database_url: str = ""
    chromadb_path: str = "./chroma_db"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env.dev"
        env_file_encoding = "utf-8"

settings = Settings()