"""Backend API configuration — reads settings from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Required environment variables:
        SUPABASE_URL: URL of your Supabase project
        SUPABASE_SERVICE_KEY: Supabase service role key
        LLMEVAL_API_KEY: API key for authenticating runner/frontend requests
    """

    supabase_url: str | None = None
    supabase_service_key: str | None = None
    database_url: str | None = None
    llmeval_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
