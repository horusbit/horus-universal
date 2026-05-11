
HORUS_GLOBAL_QUALITY_PROMPT = """
You are HORUS, a premium AI operating system with specialized agents.

Global behavior:
- Deliver final usable products, not only explanations.
- Be concise, natural, warm and practical.
- Think like ChatGPT, Claude and Gemini: helpful, direct, intelligent and polished.
- Always improve the user's request internally before answering.
- Produce the best possible quality using free/open tools first.
- If a task needs a visual, create visible image links and previews.
- If a task needs code, deliver clean working code.
- If a task needs legal/business/marketing output, deliver professional documents, structure and next steps.
- If a task needs research, be clear about limits and cite or mention sources when available.
- Never sound robotic or generic.
- Never say "I cannot" when a useful workaround exists.
- Avoid long filler. Give the result first, explanation second.
- Match the user's language.

Quality standard:
1. Understand the real goal.
2. Route to the best agent.
3. Produce a finished deliverable.
4. Include improvements or variations when useful.
5. Keep responses elegant, short and useful.

Visual standard:
For logos, images, architecture, mockups, UI, posters, flyers, branding, renders or visual concepts:
- Generate Pollinations Flux image URLs.
- Use markdown image syntax.
- Provide 2 or 3 variations when possible.
- Use professional prompt enhancement.
- Never only give Canva/Midjourney instructions.
"""



from urllib.parse import quote


VISUAL_KEYWORDS = [
    "logo",
    "image",
    "imagen",
    "visual",
    "branding",
    "architecture",
    "arquitectura",
    "render",
    "mockup",
    "ui",
    "poster",
    "flyer",
    "design",
    "diseno",
    "diseño",
    "house",
    "casa",
]


def _is_visual_request(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    return any(k in text for k in VISUAL_KEYWORDS)


def _build_pollinations_markdown(prompt: str) -> str:
    encoded = quote(prompt)

    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&enhance=true&nologo=true"

    return f"""
![Generated Image]({url})

Visual generated for:
{prompt}
"""



GLOBAL_VISUAL_RULE = """
If the user asks for:
- logos
- architecture
- renders
- mockups
- visual concepts
- engineering visuals
- branding
- posters
- flyers
- UI
- app concepts
- images

Then:
- ALWAYS generate a Pollinations image URL.
- ALWAYS show it using markdown image syntax.

Example:

![Generated Image](https://image.pollinations.ai/prompt/modern%20logo?width=1024&height=1024&enhance=true&nologo=true)

NEVER say:
"I cannot generate images."
"""

"""
OpenRouter service â€” native models array fallback.
Una sola llamada; OpenRouter maneja el failover internamente.
NOTA: No usar "route": "fallback" â€” ese campo no existe y causa HTTP 400.
      Solo "models" array es suficiente para fallback nativo.
Modelos actualizados a mayo 2026.
"""
import httpx
import json
from typing import AsyncGenerator, List, Optional
from config import settings
from models.schemas import Message, ModelTier
import logging

logger = logging.getLogger(__name__)

# Modelos gratuitos vigentes en OpenRouter (mayo 2026)
# openrouter/free = auto-router que elige el mejor modelo free disponible
FALLBACK_MODELS = [
    "openrouter/free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
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
    for m in settings.fallback_models_list:
        if m not in models:
            models.append(m)
    if primary and primary in models:
        models.remove(primary)
        models.insert(0, primary)
    elif primary and primary not in models:
        models.insert(0, primary)
    return models



# HORUS_QUALITY_INJECTED
def _normalize_messages(messages):
    normalized = []

    for msg in messages:
        if isinstance(msg, dict):
            normalized.append(msg)
        elif hasattr(msg, "model_dump"):
            normalized.append(msg.model_dump())
        elif hasattr(msg, "dict"):
            normalized.append(msg.dict())
        else:
            normalized.append({
                "role": getattr(msg, "role", "user"),
                "content": getattr(msg, "content", str(msg))
            })

    has_system = any(isinstance(m, dict) and m.get("role") == "system" for m in normalized)
    if has_system:
        for m in normalized:
            if isinstance(m, dict) and m.get("role") == "system":
                m["content"] = HORUS_GLOBAL_QUALITY_PROMPT + "\n\n" + str(m.get("content", ""))
                break
    else:
        normalized.insert(0, {"role": "system", "content": HORUS_GLOBAL_QUALITY_PROMPT})

    return normalized



HORUS_STYLE_SYSTEM_PROMPT = """
You are HORUS / ATLAS, a premium AI assistant.

Style:
- Be warm, natural, concise and useful.
- Respond like ChatGPT, Claude or Gemini: clear, empathetic and human.
- Keep answers short by default.
- Expand only when the user asks for detail.
- Avoid robotic, corporate or overly formal language.
- Avoid excessive bullet points and long introductions.
- Prioritize direct action, clarity and practical help.
- Match the user's language.
"""

# HORUS_QUALITY_INJECTED
def _normalize_messages(messages):
    normalized = []

    for msg in messages:
        if isinstance(msg, dict):
            normalized.append(msg)
        elif hasattr(msg, "model_dump"):
            normalized.append(msg.model_dump())
        elif hasattr(msg, "dict"):
            normalized.append(msg.dict())
        else:
            normalized.append({
                "role": getattr(msg, "role", "user"),
                "content": getattr(msg, "content", str(msg))
            })

    # Add HORUS conversational style layer only if no system message exists
    has_system = any(m.get("role") == "system" for m in normalized if isinstance(m, dict))
    if not has_system:
        normalized.insert(0, {
            "role": "system",
            "content": HORUS_STYLE_SYSTEM_PROMPT
        })

    return normalized


def _build_payload(models_list, messages, temperature, max_tokens, stream=False):
    selected_model = models_list[0] if isinstance(models_list, list) and len(models_list) > 0 else "openrouter/free"

    payload = {
        "model": selected_model,
        "messages": _normalize_messages(messages),
        "temperature": 0.7,
        "max_tokens": min(max_tokens or 700, 700),
        "stream": stream,
    }

    return payload


async def chat_completion(
    messages: List[Message],
    model: Optional[str] = None,
    tier: Optional[ModelTier] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    """Completion con fallback nativo OpenRouter."""
    primary = model or MODEL_MAP.get(tier, settings.MODEL_PRIMARY)
    models_list = _build_models_list(primary)[:3]
    payload = _build_payload(models_list, messages, temperature, max_tokens)

    logger.info(f"[OpenRouter] Completion -> {models_list[0]} (+{len(models_list)-1} fallbacks)")

    try:
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            response = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=_get_headers(),
                json=payload,
            )

        if response.status_code != 200:
            body = response.text[:400]
            logger.error(f"[OpenRouter] HTTP {response.status_code}: {body}")
            raise Exception(f"OpenRouter HTTP {response.status_code}: {body}")

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
    """Streaming con fallback nativo OpenRouter."""
    primary = model or MODEL_MAP.get(tier, settings.MODEL_PRIMARY)
    models_list = _build_models_list(primary)[:3]
    payload = _build_payload(models_list, messages, temperature, max_tokens, stream=True)

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
                    logger.error(f"[OpenRouter] Stream HTTP {response.status_code}: {body[:400]}")
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
        try:
            result = await chat_completion(messages, model, tier, temperature, max_tokens)
            yield result["content"]
        except Exception as e2:
            yield f"\n\nError: {str(e2)}"


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



