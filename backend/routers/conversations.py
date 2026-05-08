"""
Router de Conversaciones — Historial persistente HORUS
Redis = caché rápido | Supabase = persistencia permanente por usuario
"""
from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from services.redis_cache import cache
from services.supabase_db import (
    get_conversations, get_conversation_messages,
    update_conversation_title, delete_conversation,
    search_conversations, create_share_token,
)
from auth.supabase_auth import get_optional_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    last_message: Optional[str] = None
    agent: Optional[str] = None


@router.get("/", response_model=List[ConversationSummary])
async def list_conversations(user=Depends(get_optional_user)):
    """Lista las conversaciones del usuario autenticado desde Supabase."""
    try:
        if user:
            rows = await get_conversations(user.id)
            result = []
            for row in rows:
                msgs = await cache.get_conversation(row["id"])
                last_msg = next(
                    (m.content[:80] for m in reversed(msgs) if m.role == "user"), ""
                ) if msgs else ""
                result.append(ConversationSummary(
                    id=row["id"],
                    title=row["title"],
                    message_count=len(msgs),
                    last_message=last_msg,
                    agent=row.get("agent", "atlas"),
                ))
            return result
        else:
            summaries = await cache.list_conversations()
            return [ConversationSummary(**s) for s in summaries]
    except Exception as e:
        logger.error(f"Error listando conversaciones: {e}")
        return []


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, user=Depends(get_optional_user)):
    """Obtiene mensajes — primero Redis, luego Supabase como fallback."""
    messages = await cache.get_conversation(conversation_id)

    if not messages and user:
        messages = await get_conversation_messages(conversation_id)
        for m in messages:
            await cache.append_message(conversation_id, m)

    title = await cache.get_conversation_title(conversation_id) or "Conversación"

    return {
        "id": conversation_id,
        "title": title,
        "messages": [m.model_dump() for m in messages],
        "message_count": len(messages),
    }


@router.post("/{conversation_id}/title")
async def set_title(
    conversation_id: str,
    body: dict,
    user=Depends(get_optional_user),
):
    """Actualiza el título en Redis y Supabase."""
    title = body.get("title", "Conversación")
    await cache.set_conversation_title(conversation_id, title)
    if user:
        await update_conversation_title(conversation_id, title, user.id)
    return {"conversation_id": conversation_id, "title": title}


@router.get("/search")
async def search_convs(
    q: str,
    user=Depends(get_optional_user),
):
    """Busca conversaciones del usuario por título."""
    if not user or not q.strip():
        return []
    try:
        rows = await search_conversations(user.id, q.strip())
        result = []
        for row in rows:
            msgs = await cache.get_conversation(row["id"])
            result.append(ConversationSummary(
                id=row["id"],
                title=row["title"],
                message_count=len(msgs),
                last_message="",
                agent=row.get("agent", "atlas"),
            ))
        return result
    except Exception as e:
        logger.error(f"Error buscando conversaciones: {e}")
        return []


@router.post("/{conversation_id}/share")
async def share_conversation(
    conversation_id: str,
    user=Depends(get_optional_user),
):
    """Genera un enlace público para compartir la conversación."""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida.")
    token = await create_share_token(conversation_id, user.id)
    if not token:
        raise HTTPException(status_code=500, detail="No se pudo crear el enlace.")
    return {
        "token": token,
        "share_url": f"/share/{token}",
    }


@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    user=Depends(get_optional_user),
):
    """Elimina conversación de Redis y Supabase."""
    await cache.delete_conversation(conversation_id)
    if user:
        await delete_conversation(conversation_id, user.id)
    return {"message": "Conversación eliminada", "conversation_id": conversation_id}
