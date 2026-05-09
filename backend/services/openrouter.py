"""
OpenRouter service — usa fallback nativo de OpenRouter (models array + route:fallback)
Una sola llamada API; OpenRouter maneja el failover internamente en ms.
"""
import httpx
import json
import asyncio
from typing import AsyncGenerator, List, Optional
from config import settings
from models.schemas import Message, ModelTier
import logging

logger = logging.getLogger(__name__)

# Lista de modelos en orden de preferencia — OpenRouter los prueba en orden automáticamente
FALLBACK_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
    "qwen/qwen3-14b:free",
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

MODEL_MAP = {
    ModelTier.FREE_FAST: settings.MODEL_FAST,
    ModelTier.FREE_BALANCED: settings.MODEL_BALANCED,
    ModelTier.FREE_DEEP: settings.MODEL_DEEP,
    ModelTier.PAID_CRITICAL: settings.MODEL_CRITICAL,
}


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://horus-universal.vercel.app",
        "X-Title": "HORUS Universal",
        "Content-Type": "application/json",
    }


def _build_models_list(primary: Optional[str] = None) -> List[str]:
    """Construye lista de modelos con el primario al frente."""
    models = list(FALLBACK_MODELS)
    # Añadir modelos extra del config si no están ya
    for m in settings.fallback_models_list:
        if m not in models:
            models.append(m)
    # Poner el modelo primario al frente si se especificó
    if primary and primary in models:
        models.remove(primary)
        models.insert(0, primary)
    elif primary and primary not in models:
        models.insert(0, primary)
    return models


async def chat_completion(
    messages: List[Message],
    model: Optional[str] = None,
    tier: Optional[ModelTier] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    """
    Completion usando OpenRouter native fallback.
    Pasa 'models' array — OpenRouter prueba cada modelo en orden sin latencia extra.
    """
    primary = model or MODEL_MAP.get(tier, settings.MODEL_PRIMARY)
    models_list = _build_models_list(primary)

    payload = {
        "models": models_list,          # OpenRouter native fallback
        "route": "fallback",
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            response = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=_get_headers(),
                json=payload,
            )

        if response.status_code != 200:
            logger.error(f"[OpenRouter] HTTP {response.status_code}: {response.text[:200]}")
            raise Exception(f"OpenRouter HTTP {response.status_code}")

        data = response.json()

        if "error" in data:
            msg = data["error"].get("message", str(data["error"]))
            logger.error(f"[OpenRouter] API error: {msg}")
            raise Exception(f"OpenRouter: {msg}")

        content = data["choices"][0]["message"].get("content") or ""
        model_used = data.get("model", models_list[0])
        logger.info(f"[OpenRouter] ok {model_used} ({len(content)} chars)")
        return {"content": content, "model": model_used, "usage": data.get("usage", {})}

    except httpx.TimeoutException:
        raise Exception("Tiempo de espera agotado. El servidor esta ocupado, intenta de nuevo.")
    except Exception as e:
        if "OpenRouter" in str(e) or "Tiempo" in str(e):
            raise
        raise Exception(f"Error conectando con IA: {str(e)}")


async def chat_stream(
    messages: List[Message],
    model: Optional[str] = None,
    tier: Optional[ModelTier] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    """
    Streaming usando OpenRouter native fallback.
    Misma estrategia: 'models' array + route:fallback.
    """
    primary = model or MODEL_MAP.get(tier, settings.MODEL_PRIMARY)
    models_list = _build_models_list(primary)

    payload = {
        "models": models_list,
        "route": "fallback",
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    logger.info(f"[OpenRouter] Stream -> {models_list[0]} (+{len(models_list)-1} fallbacks)")

    try:
        async with httpx.AsyncClient(timeout=90.0, trust_env=False) as client:
            async with client.stream(
                "POST",
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=_get_headers(),
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.error(f"[OpenRouter] Stream HTTP {response.status_code}: {body[:200]}")
                    # Fallback a completion no-stream
                    result = await chat_completion(messages, model, tier, temperature, max_tokens)
                    yield result["content"]
                    return

                chunk_count = 0
                buffer = ""
                model_used = models_list[0]

                async for raw in response.aiter_bytes():
                    buffer += raw.decode("utf-8", errors="replace")
                    lines = buffer.split("\n")
                    buffer = lines.pop()

                    for line in lines:
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)

                            # Capturar modelo usado (OpenRouter lo incluye en el stream)
                            if data.get("model"):
                                model_used = data["model"]

                            if "error" in data:
                                err_msg = data["error"].get("message", "Error desconocido")
                                logger.error(f"[OpenRouter] Stream error: {err_msg}")
                                yield f"\n\nError: {err_msg}"
                                return

                            choices = data.get("choices", [])
                            if not choices:
                                continue
                            content = (choices[0].get("delta") or {}).get("content") or ""
                            if content:
                                chunk_count += 1
                                yield content

                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

                logger.info(f"[OpenRouter] ok Stream {model_used} ({chunk_count} chunks)")

    except httpx.TimeoutException:
        yield "\n\nTiempo de espera agotado. Intenta de nuevo."
    except Exception as e:
        logger.error(f"[OpenRouter] Stream exception: {e}")
        # Ultimo recurso: completion sincrona
        try:
            result = await chat_completion(messages, model, tier, temperature, max_tokens)
            yield result["content"]
        except Exception as e2:
            yield f"\n\nError: {str(e2)}"


# Mantener compatibilidad con imports que usan select_model
def select_model(tier: Optional[ModelTier] = None, task_complexity: str = "medium") -> str:
    if tier:
        return MODEL_MAP.get(tier, settings.MODEL_PRIMARY)
    complexity_map = {
        "simple": ModelTier.FREE_FAST,
        "medium": ModelTier.FREE_BALANCED,
        "complex": ModelTier.FREE_DEEP,
        "critical": ModelTier.PAID_CRITICAL,
    }
    return MODEL_MAP.get(complexity_map.get(task_complexity, ModelTier.FREE_BALANCED), settings.MODEL_PRIMARY)
