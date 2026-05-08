"""
Router de Imágenes — HORUS Universal
Generación de imágenes gratis via Pollinations.ai (sin API key)
También soporta Replicate si REPLICATE_API_TOKEN está configurado.
"""
import urllib.parse
import hashlib
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth.supabase_auth import get_optional_user
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    model: str = "flux"          # flux | flux-realism | flux-anime | flux-3d | turbo
    nologo: bool = True
    enhance: bool = True


class ImageResponse(BaseModel):
    url: str
    prompt: str
    model: str
    width: int
    height: int


@router.post("/generate", response_model=ImageResponse)
async def generate_image(
    body: ImageRequest,
    user=Depends(get_optional_user),
):
    """
    Genera una imagen con Pollinations.ai (gratis, sin API key).
    Devuelve la URL directa de la imagen.
    """
    if not body.prompt or len(body.prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="El prompt es muy corto.")

    # Limpiar y encodear el prompt
    clean_prompt = body.prompt.strip()[:500]
    encoded = urllib.parse.quote(clean_prompt, safe="")

    # Construir URL de Pollinations
    seed = int(hashlib.md5(clean_prompt.encode()).hexdigest()[:8], 16) % 999999

    url = (
        f"{POLLINATIONS_BASE}/{encoded}"
        f"?width={body.width}"
        f"&height={body.height}"
        f"&model={body.model}"
        f"&seed={seed}"
        f"&nologo={str(body.nologo).lower()}"
        f"&enhance={str(body.enhance).lower()}"
    )

    # Verificar que Pollinations responde (HEAD request rápido)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.head(url, follow_redirects=True)
            if r.status_code not in (200, 301, 302):
                logger.warning(f"[Images] Pollinations HEAD {r.status_code}")
    except Exception as e:
        logger.warning(f"[Images] Pollinations check error: {e}")
        # No fallar — la URL puede funcionar igual

    logger.info(f"[Images] Generated: model={body.model}, size={body.width}x{body.height}")
    return ImageResponse(
        url=url,
        prompt=clean_prompt,
        model=body.model,
        width=body.width,
        height=body.height,
    )


@router.get("/models")
async def list_models():
    """Lista los modelos de imagen disponibles en Pollinations."""
    return {
        "models": [
            {"id": "flux",          "name": "Flux",           "desc": "General purpose, alta calidad"},
            {"id": "flux-realism",  "name": "Flux Realism",   "desc": "Fotorrealista"},
            {"id": "flux-anime",    "name": "Flux Anime",     "desc": "Estilo anime/manga"},
            {"id": "flux-3d",       "name": "Flux 3D",        "desc": "Renders 3D"},
            {"id": "flux-cablyai",  "name": "Flux Cably",     "desc": "Artístico"},
            {"id": "turbo",         "name": "Turbo",          "desc": "Rápido, menor calidad"},
        ],
        "provider": "Pollinations.ai",
        "cost": "free",
    }
