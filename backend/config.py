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

    # Voz
    GROQ_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # Google Drive OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APP_BASE_URL: str = "https://horus-backend.onrender.com"
    FRONTEND_URL: str = "https://horus-universal.vercel.app"

    # Web Search
    TAVILY_API_KEY: str = ""
    BRAVE_SEARCH_API_KEY: str = ""

    # Telegram bot
    TELEGRAM_BOT_TOKEN: str = ""

    # Lemon Squeezy
    LEMONSQUEEZY_API_KEY: str = ""
    LEMONSQUEEZY_STORE_ID: str = ""
    LEMONSQUEEZY_VARIANT_ID: str = ""
    LEMONSQUEEZY_WEBHOOK_SECRET: str = ""

    # Email (para notificaciones Teams)
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "HORUS Universal <noreply@horusai.app>"

    # Modelos activos — actualizados mayo 2026
    # openrouter/free = auto-router que elige el mejor modelo free disponible
    MODEL_PRIMARY: str = "openrouter/free"
    MODEL_FAST: str = "openrouter/free"
    MODEL_BALANCED: str = "openrouter/free"
    MODEL_CRITICAL: str = "openai/gpt-oss-120b:free"
    MODEL_DEEP: str = "nvidia/nemotron-3-super-120b-a12b:free"
    MODEL_FALLBACKS: str = "openrouter/free,openai/gpt-oss-120b:free,nvidia/nemotron-3-super-120b-a12b:free,qwen/qwen3-next-80b-a3b-instruct:free,google/gemma-4-31b-it:free,nousresearch/hermes-3-llama-3.1-405b:free,nvidia/nemotron-3-nano-30b-a3b:free,openai/gpt-oss-20b:free,meta-llama/llama-3.2-3b-instruct:free"

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
