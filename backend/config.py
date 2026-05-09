from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "HORUS Universal"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,https://horus-universal.vercel.app,https://horus-universal-git-main-horusbits-projects.vercel.app"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # OpenRouter
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # Gemini backup
    GEMINI_API_KEY: str = ""

    # Voz - Fase 2
    GROQ_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # Google Drive OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APP_BASE_URL: str = "https://horus-backend.onrender.com"
    FRONTEND_URL: str = "https://horus-universal.vercel.app"

    # Web Search (Tavily — 1000/mes gratis: https://tavily.com)
    TAVILY_API_KEY: str = ""
    BRAVE_SEARCH_API_KEY: str = ""  # legacy

    # Telegram bot
    TELEGRAM_BOT_TOKEN: str = ""

    # Lemon Squeezy - Fase 6
    LEMONSQUEEZY_API_KEY: str = ""
    LEMONSQUEEZY_STORE_ID: str = ""
    LEMONSQUEEZY_VARIANT_ID: str = ""
    LEMONSQUEEZY_WEBHOOK_SECRET: str = ""

    # Modelos activos
    MODEL_PRIMARY: str = "google/gemini-2.0-flash-exp:free"
    MODEL_FAST: str = "google/gemini-2.0-flash-exp:free"
    MODEL_BALANCED: str = "google/gemini-2.0-flash-exp:free"
    MODEL_CRITICAL: str = "google/gemini-2.0-flash-thinking-exp:free"
    MODEL_DEEP: str = "meta-llama/llama-3.3-70b-instruct:free"
    MODEL_FALLBACKS: str = "google/gemini-flash-1.5:free,google/gemma-3-27b-it:free,google/gemma-3-12b-it:free,meta-llama/llama-3.3-70b-instruct:free,meta-llama/llama-3.1-8b-instruct:free,deepseek/deepseek-chat:free,qwen/qwen3-14b:free,mistralai/mistral-7b-instruct:free,microsoft/phi-3-mini-128k-instruct:free"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def fallback_models_list(self) -> List[str]:
        return [m.strip() for m in self.MODEL_FALLBACKS.split(",") if m.strip()]

    @property
    def voice_enabled(self) -> bool:
        return bool(self.GROQ_API_KEY or self.ELEVENLABS_API_KEY)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
