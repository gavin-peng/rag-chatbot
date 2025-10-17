from rag_chatbot.config import settings

print(f"Database URL: {settings.database_url}")
print(f"Google API Key: {settings.google_api_key[:10] if settings.google_api_key else 'None'}...")
print(f"All settings: {settings.model_dump()}")
