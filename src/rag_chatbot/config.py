import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    google_api_key: str = ""
    database_url: str = ""
    chromadb_path: str = "./chroma_db"
    log_level: str = "INFO"
    
    # Agent configuration
    default_agent: str = "qa_agent"

    # Model configurations
    qa_agent_model: str = "gemini-2.5-flash"
    code_assistant_model: str = "gemini-2.5-flash" 
    workflow_agent_model: str = "gemini-2.5-flash"

    # Temperature settings
    qa_agent_temperature: float = 0.7
    code_assistant_temperature: float = 0.2
    workflow_agent_temperature: float = 0.3

    # Search and features
    max_search_results: int = 10
    vector_collection_name: str = "rag_documents"
    enable_code_execution: bool = False
    enable_state_management: bool = True
    enable_agent_switching: bool = True
    conversation_memory_size: int = 10

    # Server settings (if not already present)
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Logging
    log_agent_switches: bool = True
    log_search_queries: bool = True
    
    class Config:
        env_file = ".env.dev"
        env_file_encoding = "utf-8"

settings = Settings()