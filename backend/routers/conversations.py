"""
Router de Conversaciones - Historial y memoria persistente de HORUS
"""
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from services.redis_cache import cache
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


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list


@router.get("/", response_model=List[ConversationSummary])
async def list_conversations(user=Depends(get_optional_user)):
    """Lista todas las conversaciones guardadas."""
    try:
        summaries = await cache.list_conversations()
        return summaries
    except Exception as e:
        logger.error(f"Error listando conversaciones: {e}")
        return []


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, user=Depends(get_optional_user)):
    """Obtiene el detalle de una conversación."""
    messages = await cache.get_conversation(conversation_id)
    title = await cache.get_conversation_title(conversation_id)
    return {
        "id": conversation_id,
        "title": title or "Conversación",
        "messages": [m.model_dump() for m in messages],
        "message_count": len(messages),
    }


@router.post("/{conversation_id}/title")
async def set_conversation_title(
    conversation_id: str,
    body: dict,
    user=Depends(get_optional_user)
):
    """Establece el título de una conversación."""
    title = body.get("title", "Conversación")
    await cache.set_conversation_title(conversation_id, title)
    return {"conversation_id": conversation_id, "title": title}
