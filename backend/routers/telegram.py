"""
Router Telegram — Bot HORUS Universal
Recibe webhooks de Telegram y responde usando el agente ATLAS.
Configurar: TELEGRAM_BOT_TOKEN en variables de entorno.
Webhook: POST https://<tu-backend>/api/v1/telegram/webhook
"""
import httpx
import logging
from fastapi import APIRouter, Request, HTTPException
from config import settings
from agents import get_agent
from models.schemas import AgentType, Message
from services.memory import get_user_memory, extract_and_save_facts, build_memory_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

TELEGRAM_API = "https://api.telegram.org"
MAX_MESSAGE_LEN = 4096  # Límite de Telegram


async def send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown"):
    """Envía un mensaje a Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("[Telegram] TELEGRAM_BOT_TOKEN no configurado.")
        return

    # Telegram tiene límite de 4096 chars — truncar si es necesario
    if len(text) > MAX_MESSAGE_LEN:
        text = text[:MAX_MESSAGE_LEN - 20] + "\n\n_(Respuesta truncada)_"

    url = f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, json=payload)
            if r.status_code != 200:
                # Reintentar sin parse_mode si hay error de formato
                payload_plain = {"chat_id": chat_id, "text": text}
                await client.post(url, json=payload_plain)
    except Exception as e:
        logger.error(f"[Telegram] send error: {e}")


async def send_typing(chat_id: int):
    """Envía 'escribiendo...' como feedback visual."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    url = f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/sendChatAction"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"chat_id": chat_id, "action": "typing"})
    except Exception:
        pass


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Recibe actualizaciones de Telegram.
    Registrar este endpoint como webhook con:
      POST https://api.telegram.org/bot<TOKEN>/setWebhook
      {"url": "https://<tu-backend>/api/v1/telegram/webhook"}
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram bot no configurado.")

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    # Extraer mensaje del update
    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}  # Ignorar otros tipos de update

    chat_id = message["chat"]["id"]
    user_id_tg = str(message["from"]["id"])
    first_name = message["from"].get("first_name", "")
    text = message.get("text", "").strip()

    if not text:
        return {"ok": True}

    # Comando /start
    if text.startswith("/start"):
        welcome = (
            f"👁 *¡Hola {first_name}! Soy HORUS Universal.*\n\n"
            "Soy un orquestador de IA con 16 agentes especializados.\n\n"
            "Puedo ayudarte con:\n"
            "• 💻 Código y programación\n"
            "• 📊 Análisis de datos\n"
            "• ✍️ Marketing y contenido\n"
            "• ⚖️ Consultas legales\n"
            "• 🔮 Estrategia de negocios\n"
            "• 🎨 Diseño e imágenes\n"
            "• Y mucho más...\n\n"
            "Simplemente escríbeme lo que necesitas."
        )
        await send_telegram_message(chat_id, welcome)
        return {"ok": True}

    # Comando /help
    if text.startswith("/help"):
        help_text = (
            "👁 *HORUS Universal — Comandos*\n\n"
            "/start — Bienvenida\n"
            "/help — Esta ayuda\n"
            "/agentes — Lista de agentes disponibles\n\n"
            "O simplemente escribe tu mensaje y ATLAS te enruta al mejor agente."
        )
        await send_telegram_message(chat_id, help_text)
        return {"ok": True}

    # Comando /agentes
    if text.startswith("/agentes"):
        agents_text = (
            "🤖 *Agentes HORUS disponibles:*\n\n"
            "🌐 ATLAS — Orquestador (auto-routing)\n"
            "⚡ CIPHER — Código y DevOps\n"
            "✨ NOVA — Marketing y contenido\n"
            "⚖️ LEXIS — Legal\n"
            "🔮 ORACLE — Estrategia de negocio\n"
            "🌍 HERMES — Traducción\n"
            "🎙️ ECHO — Audio y podcasts\n"
            "🔬 DARWIN — Investigación\n"
            "🎨 PIXEL — Diseño e imágenes\n"
            "📡 NEXUS — Redes sociales\n"
            "📊 FORGE — Datos y Excel\n"
            "🎓 SAGE — Educación\n"
            "💼 VECTOR — Ventas\n"
            "⏱️ CHRONOS — Productividad\n"
            "🏛️ POLITEIA — Política\n"
            "🏫 EDUCRAFT — Plataformas educativas"
        )
        await send_telegram_message(chat_id, agents_text)
        return {"ok": True}

    # Mensaje normal — procesar con ATLAS (auto-routing)
    await send_typing(chat_id)

    try:
        # Usar user_id_tg como identificador de memoria (prefijo "tg_")
        tg_user_key = f"tg_{user_id_tg}"
        memory = await get_user_memory(tg_user_key)
        memory_context = build_memory_context(memory)
        await extract_and_save_facts(tg_user_key, text)

        from services.router import detect_agent
        effective_agent = detect_agent(text, AgentType.ATLAS)
        agent_class = get_agent(effective_agent)

        result = await agent_class.respond(
            user_message=text,
            history=[],
            extra_system_context=memory_context,
        )

        response_text = result.get("content", "Sin respuesta del agente.")

        # Quitar bloques [HORUS_IMAGE] del texto de Telegram (no renderizables)
        import re
        response_text = re.sub(r'\[HORUS_IMAGE\].*?\[/HORUS_IMAGE\]', '🎨 _[Imagen generada - visítanos en web para verla]_', response_text, flags=re.DOTALL)

        await send_telegram_message(chat_id, response_text)

    except Exception as e:
        logger.error(f"[Telegram] processing error: {e}")
        await send_telegram_message(chat_id, "⚠️ Error procesando tu mensaje. Intenta de nuevo.")

    return {"ok": True}


@router.post("/set-webhook")
async def set_webhook(request: Request):
    """Configura el webhook de Telegram apuntando a este servidor."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN no configurado.")

    body = await request.json()
    backend_url = body.get("url")
    if not backend_url:
        raise HTTPException(status_code=400, detail="Falta el campo 'url'.")

    webhook_url = f"{backend_url.rstrip('/')}/api/v1/telegram/webhook"

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
            json={"url": webhook_url},
        )
        data = r.json()

    return {
        "ok": data.get("ok"),
        "description": data.get("description"),
        "webhook_url": webhook_url,
    }


@router.get("/info")
async def bot_info():
    """Devuelve información del bot configurado."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"configured": False, "message": "TELEGRAM_BOT_TOKEN no configurado."}

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/getMe")
        data = r.json()

    return {
        "configured": True,
        "bot": data.get("result", {}),
        "webhook_endpoint": "/api/v1/telegram/webhook",
    }
