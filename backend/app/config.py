from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str = "AQ.Ab8RN6KP39NbjIiVCFEY9WvBshn9AAuYMLzpKF200VW1RCxljg"

    gemini_model: str = "gemini-3-flash-preview"

    gemini_fallback_models: str = (
        "gemini-3.1-flash-lite,"
        "gemini-3.5-flash,"
        "gemini-flash-latest"
    )

    # GitHub API
    github_token: str = ""

    # Frontend URL for CORS
    frontend_origin: str = "https://skifrontend.vercel.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
