"""
Router de Voz - HORUS Universal Fase 2
STT: Groq Whisper (si GROQ_API_KEY disponible) → Browser Web Speech API (fallback)
TTS: ElevenLabs (premium) → Edge TTS (fallback gratis)
"""
import io
import httpx
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str | None = None   # override del voice_id por defecto
    language: str = "es"           # para Edge TTS fallback


# ── STT: Transcripción con Groq Whisper ───────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(default="es"),
):
    """
    Recibe un archivo de audio (webm/mp4/wav/m4a) y devuelve la transcripción.
    Usa Groq Whisper si GROQ_API_KEY está configurado.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="use_browser_stt"
        )

    audio_bytes = await audio.read()
    filename = audio.filename or "audio.webm"

    logger.info(f"🎙️ Transcribiendo audio: {filename} ({len(audio_bytes)} bytes)")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                files={"file": (filename, audio_bytes, audio.content_type or "audio/webm")},
                data={
                    "model": "whisper-large-v3-turbo",
                    "language": language,
                    "response_format": "json",
                },
            )

        if response.status_code != 200:
            logger.error(f"Groq error {response.status_code}: {response.text}")
            raise HTTPException(status_code=502, detail=f"Error de Groq: {response.text}")

        result = response.json()
        transcript = result.get("text", "").strip()
        logger.info(f"✅ Transcripción: {transcript[:80]}...")

        return {"transcript": transcript, "language": language}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Tiempo de espera agotado en Groq Whisper.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise HTTPException(status_code=500, detail=f"Error al transcribir: {str(e)}")


# ── TTS: Síntesis de voz ───────────────────────────────────────────────────────

@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Convierte texto en audio.
    Prioridad: ElevenLabs → Edge TTS (fallback gratis).
    """
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    # Limitar longitud para evitar costos excesivos
    if len(text) > 2000:
        text = text[:2000]

    if settings.ELEVENLABS_API_KEY:
        return await _synthesize_elevenlabs(text, request.voice_id or settings.ELEVENLABS_VOICE_ID)
    else:
        return await _synthesize_edge_tts(text, request.language)


async def _synthesize_elevenlabs(text: str, voice_id: str) -> StreamingResponse:
    """Síntesis con ElevenLabs (premium, voz muy natural)."""
    logger.info(f"🔊 ElevenLabs TTS: {len(text)} chars, voice={voice_id}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True,
                    },
                },
            )

        if response.status_code != 200:
            logger.warning(f"ElevenLabs error {response.status_code}, fallback a Edge TTS")
            return await _synthesize_edge_tts(text)

        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=horus_speech.mp3"},
        )

    except Exception as e:
        logger.warning(f"ElevenLabs falló ({e}), usando Edge TTS fallback")
        return await _synthesize_edge_tts(text)


async def _synthesize_edge_tts(text: str, language: str = "es") -> StreamingResponse:
    """
    Síntesis con Edge TTS de Microsoft (completamente gratis).
    Requiere: pip install edge-tts
    """
    try:
        import edge_tts  # type: ignore

        # Seleccionar voz según idioma
        voice_map = {
            "es": "es-ES-AlvaroNeural",
            "en": "en-US-AriaNeural",
            "fr": "fr-FR-HenriNeural",
            "pt": "pt-BR-AntonioNeural",
            "de": "de-DE-KillianNeural",
        }
        voice = voice_map.get(language[:2], "es-ES-AlvaroNeural")

        logger.info(f"🔊 Edge TTS: {len(text)} chars, voice={voice}")

        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if not audio_data:
            raise ValueError("Edge TTS no generó audio")

        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=horus_speech.mp3"},
        )

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="TTS no disponible: instala edge-tts (pip install edge-tts) o configura ELEVENLABS_API_KEY."
        )
    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en síntesis de voz: {str(e)}")


# ── Info del servicio de voz ───────────────────────────────────────────────────

@router.get("/status")
async def voice_status():
    """Devuelve el estado de los servicios de voz disponibles."""
    return {
        "stt": {
            "provider": "Groq Whisper" if settings.GROQ_API_KEY else "Browser Web Speech API (fallback)",
            "model": "whisper-large-v3-turbo" if settings.GROQ_API_KEY else "native",
            "enabled": True,
            "server_stt": bool(settings.GROQ_API_KEY),
            "endpoint": "/api/v1/voice/transcribe",
        },
        "tts": {
            "provider": "ElevenLabs" if settings.ELEVENLABS_API_KEY else "Edge TTS (Microsoft)",
            "voice_id": settings.ELEVENLABS_VOICE_ID if settings.ELEVENLABS_API_KEY else "es-ES-AlvaroNeural",
            "enabled": True,
            "endpoint": "/api/v1/voice/synthesize",
        },
    }
