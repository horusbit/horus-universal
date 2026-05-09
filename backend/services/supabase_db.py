"""
Supabase DB — Persistencia permanente de conversaciones HORUS
Redis = caché rápido (7 días) | Supabase = historial permanente por usuario
"""
import uuid
from typing import List, Optional
from config import settings
from models.schemas import Message
import logging

logger = logging.getLogger(__name__)


def _get_client():
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY)


# ── Conversaciones ───────────────────────────────────────────────────────────

async def create_conversation(user_id: str, title: str = "Nueva conversación", agent: str = "atlas") -> Optional[str]:
    """Crea una conversación en Supabase y devuelve su ID."""
    try:
        client = _get_client()
        result = client.table("conversations").insert({
            "user_id": user_id,
            "title": title,
            "agent": agent,
        }).execute()
        if result.data:
            return result.data[0]["id"]
    except Exception as e:
        logger.error(f"[SupabaseDB] create_conversation error: {e}")
    return None


async def get_conversations(user_id: str, limit: int = 50) -> list:
    """Lista las conversaciones de un usuario ordenadas por última actualización."""
    try:
        client = _get_client()
        result = client.table("conversations") \
            .select("id, title, agent, updated_at") \
            .eq("user_id", user_id) \
            .order("updated_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"[SupabaseDB] get_conversations error: {e}")
        return []


async def get_conversations_with_counts(user_id: str, limit: int = 50) -> list:
    """Lista conversaciones con conteo real de mensajes desde Supabase (sin depender de Redis)."""
    try:
        client = _get_client()
        # Obtener conversaciones
        result = client.table("conversations") \
            .select("id, title, agent, updated_at") \
            .eq("user_id", user_id) \
            .order("updated_at", desc=True) \
            .limit(limit) \
            .execute()
        rows = result.data or []
        if not rows:
            return []

        # Para cada conversación, contar mensajes y obtener el último mensaje del usuario
        enriched = []
        for row in rows:
            try:
                count_result = client.table("messages") \
                    .select("id", count="exact") \
                    .eq("conversation_id", row["id"]) \
                    .execute()
                count = count_result.count or 0

                # Último mensaje del usuario
                last_result = client.table("messages") \
                    .select("content, role") \
                    .eq("conversation_id", row["id"]) \
                    .eq("role", "user") \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
                last_msg = last_result.data[0]["content"][:80] if last_result.data else ""

                enriched.append({
                    **row,
                    "message_count": count,
                    "last_message": last_msg,
                })
            except Exception:
                enriched.append({**row, "message_count": 0, "last_message": ""})

        return enriched
    except Exception as e:
        logger.error(f"[SupabaseDB] get_conversations_with_counts error: {e}")
        return []


async def get_conversation_messages(conversation_id: str) -> List[Message]:
    """Obtiene los mensajes de una conversación."""
    try:
        client = _get_client()
        result = client.table("messages") \
            .select("role, content, agent, model_used") \
            .eq("conversation_id", conversation_id) \
            .order("created_at") \
            .execute()
        return [Message(role=m["role"], content=m["content"]) for m in (result.data or [])]
    except Exception as e:
        logger.error(f"[SupabaseDB] get_conversation_messages error: {e}")
        return []


async def save_message(conversation_id: str, message: Message, agent: str = None, model_used: str = None) -> bool:
    """Guarda un mensaje en Supabase y actualiza updated_at de la conversación."""
    try:
        client = _get_client()
        client.table("messages").insert({
            "conversation_id": conversation_id,
            "role": message.role,
            "content": message.content,
            "agent": agent,
            "model_used": model_used,
        }).execute()
        # Actualizar timestamp de la conversación
        client.table("conversations") \
            .update({"updated_at": "now()"}) \
            .eq("id", conversation_id) \
            .execute()
        return True
    except Exception as e:
        logger.error(f"[SupabaseDB] save_message error: {e}")
        return False


async def update_conversation_title(conversation_id: str, title: str, user_id: str = None) -> bool:
    """Actualiza el título de una conversación."""
    try:
        client = _get_client()
        query = client.table("conversations").update({"title": title}).eq("id", conversation_id)
        if user_id:
            query = query.eq("user_id", user_id)
        query.execute()
        return True
    except Exception as e:
        logger.error(f"[SupabaseDB] update_conversation_title error: {e}")
        return False


async def delete_conversation(conversation_id: str, user_id: str = None) -> bool:
    """Elimina una conversación y sus mensajes (CASCADE)."""
    try:
        client = _get_client()
        query = client.table("conversations").delete().eq("id", conversation_id)
        if user_id:
            query = query.eq("user_id", user_id)
        query.execute()
        return True
    except Exception as e:
        logger.error(f"[SupabaseDB] delete_conversation error: {e}")
        return False


async def search_conversations(user_id: str, query: str, limit: int = 20) -> list:
    """Busca conversaciones del usuario por título."""
    try:
        client = _get_client()
        result = client.table("conversations") \
            .select("id, title, agent, updated_at") \
            .eq("user_id", user_id) \
            .ilike("title", f"%{query}%") \
            .order("updated_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"[SupabaseDB] search_conversations error: {e}")
        return []


async def create_share_token(conversation_id: str, user_id: str) -> Optional[str]:
    """Crea un token público para compartir una conversación. Devuelve el token."""
    try:
        token = str(uuid.uuid4())
        client = _get_client()
        client.table("shared_conversations").upsert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "token": token,
        }, on_conflict="conversation_id").execute()
        return token
    except Exception as e:
        logger.error(f"[SupabaseDB] create_share_token error: {e}")
        return None


async def get_shared_conversation(token: str) -> Optional[dict]:
    """Obtiene lo