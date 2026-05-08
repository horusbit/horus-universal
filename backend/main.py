"""
HORUS Universal - Backend Principal
FastAPI + Supabase + OpenRouter + Upstash Redis
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from config import settings
from routers import chat_router, agents_router, conversations_router, voice_router
from routers.billing import router as billing_router
from routers.files import router as files_router
from routers.admin import router as admin_router
import logging

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciando...")
    logger.info(f"📡 Modelo primario: {settings.MODEL_PRIMARY}")
    logger.info(f"🔄 Fallbacks: {settings.MODEL_FALLBACKS}")
    logger.info(f"🤖 Agentes (16): ATLAS CIPHER NOVA LEXIS ORACLE HERMES ECHO DARWIN PIXEL NEXUS FORGE SAGE VECTOR CHRONOS POLITEIA EDUCRAFT")
    logger.info(f"🎙️ Voz: {'GROQ Whisper + ElevenLabs' if settings.voice_enabled else 'No configurado (añade GROQ_API_KEY / ELEVENLABS_API_KEY)'}")
    logger.info(f"🌐 CORS: {settings.cors_origins_list}")
    yield
    logger.info("🛑 HORUS Universal detenido")


app = FastAPI(
    title="HORUS Universal API",
    description="Orquestador Personal de IA Multi-Modelo — 16 agentes especializados",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "agents": 16,
        "model_primary": settings.MODEL_PRIMARY,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "horus-backend", "version": settings.APP_VERSION}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Endpoint no encontrado", "docs": "/docs"})


@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"Error 500: {exc}")
    return JSONResponse(status_code=500, content={"error": "Error interno. Intenta de nuevo."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG, log_level="info")
