from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    github_token: str = ""
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    gemini_fallback_models: str = "gemini-3.1-flash-lite,gemini-3.5-flash,gemini-flash-latest"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings=Settings()
