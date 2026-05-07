import httpx
import json
import asyncio
from typing import AsyncGenerator, List, Optional
from config import settings
from models.schemas import Message, ModelTier
from services.model_health import mark_failed, get_available_models
import logging

logger = logging.getLogger(__name__)

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


def _build_chain(primary: str) -> List[str]:
    chain = [primary]
    for m in settings.fallback_models_list:
        if m not in chain:
            chain.append(m)
    return get_available_models(chain)


async def _single_completion(
    client: httpx.AsyncClient,
    model_id: str,
    messages: List[Message],
    temperature: float,
    max_tokens: int,
) -> Optional[dict]:
    payload = {
        "model": model_id,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        response = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=_get_headers(),
            json=payload,
        )
        if response.status_code == 429:
            logger.warning(f"[OpenRouter] {model_id} rate-limited (429)")
            mark_failed(model_id)
            return None
        if response.status_code != 200:
            logger.warning(f"[OpenRouter] {model_id} HTTP {response.status_code}")
            mark_failed(model_id)
            return None

        data = response.json()
        if "error" in data:
            code = data["error"].get("code", "?")
            logger.warning(f"[OpenRouter] {model_id} error code={code}")
            if code in (429, 503):
                mark_failed(model_id)
            return None

        content = data["choices"][0]["message"].get("content") or ""
        if not content:
            logger.warning(f"[OpenRouter] {model_id} vacío")
            return None

        logger.info(f"[OpenRouter] ✓ {model_id} ({len(content)} chars)")
        return {"content": content, "model": data.get("model", model_id), "usage": data.get("usage", {})}

    except httpx.TimeoutException:
        logger.warning(f"[OpenRouter] {model_id} timeout")
        mark_failed(model_id)
        return None
    except Exception as e:
        logger.warning(f"[OpenRouter] {model_id} excepción: {e}")
        return None


async def chat_completion(
    messages: List[Message],
    model: Optional[str] = None,
    tier: Optional[ModelTier] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    primary = model or select_model(tier)
    chain = _build_chain(primary)

    async with httpx.AsyncClient(timeout=45.0, trust_env=False) as client:
        for i, model_id in enumerate(chain):
            if i > 0:
                await asyncio.sleep(0.5)  # pequeña pausa entre intentos
            result = await _single_completion(client, model_id, messages, temperature, max_tokens)
            if result:
                return result

    raise Exception("Todos los modelos disponibles están ocupados. Por favor intenta en unos segundos.")


async def chat_stream(
    messages: List[Message],
    model: Optional[str] = None,
    tier: Optional[ModelTier] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    primary = model or select_model(tier)
    chain = _build_chain(primary)

    base_payload = {
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    for i, model_id in enumerate(chain):
        if i > 0:
            await asyncio.sleep(0.5)

        logger.info(f"[OpenRouter] Stream → {model_id}")
        success = False

        try:
            async with httpx.AsyncClient(timeout=90.0, trust_env=False) as client:
                payload = {**base_payload, "model": model_id}
                async with client.stream(
                    "POST",
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers=_get_headers(),
                    json=payload,
                ) as response:
                    if response.status_code == 429:
                        mark_failed(model_id)
                        continue
                    if response.status_code != 200:
                        mark_failed(model_id)
                        continue

                    chunk_count = 0
                    buffer = ""

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
                                if "error" in data:
                                    code = data["error"].get("code", 0)
                                    if code in (429, 503):
                                        mark_failed(model_id)
                                    break
                                choices = data.get("choices", [])
                                if not choices:
                                    continue
                                content = (choices[0].get("delta") or {}).get("content") or ""
                                if content:
                                    chunk_count += 1
                                    success = True
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue

                    if success:
                        logger.info(f"[OpenRouter] ✓ Stream {model_id} ({chunk_count} chunks)")
                        return

        except Exception as e:
            logger.warning(f"[OpenRouter] Stream {model_id} error: {e}")
            continue

    # Último recurso: usar completion normal
    logger.warning("[OpenRouter] Stream fallback → completion")
    try:
        result = await chat_completion(messages, model, tier, temperature, max_tokens)
        yield result["content"]
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"
