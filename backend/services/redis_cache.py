"""
Cache con Upstash Redis — Memoria persistente de conversaciones HORUS
Con fallback en memoria para desarrollo
"""
import json
from typing import Optional, List, Dict, Any
from config import settings
from models.schemas import Message
import logging

logger = logging.getLogger(__name__)

DEFAULT_TTL = 86400 * 7  # 7 días


class RedisCache:
    def __init__(self):
        self._client = None
        self._memory: Dict[str, Any] = {}  # fallback en RAM

    def _get_client(self):
        if self._client is None and settings.UPSTASH_REDIS_REST_URL:
            try:
                from upstash_redis import Redis
                self._client = Redis(
                    url=settings.UPSTASH_REDIS_REST_URL,
                    token=settings.UPSTASH_REDIS_REST_TOKEN,
                )
                # Test connection
                self._client.ping()
                logger.info("[Redis] Upstash conectado correctamente")
            except Exception as e:
                logger.warning(f"[Redis] No disponible: {e}. Usando memoria.")
                self._client = None
        return self._client

    def _mem_get(self, key: str):
        return self._memory.get(key)

    def _mem_set(self, key: str, value):
        self._memory[key] = value

    def _mem_del(self, key: str):
        self._memory.pop(key, None)

    # ── Conversaciones ──────────────────────────────────────────────────

    async def get_conversation(self, conversation_id: str) -> List[Message]:
        key = f"conv:{conversation_id}:messages"
        try:
            client = self._get_client()
            if client:
                data = client.get(key)
            else:
                data = self._mem_get(key)
            if data:
                msgs = json.loads(data) if isinstance(data, str) else data
                return [Message(**m) for m in msgs]
        except Exception as e:
            logger.error(f"[Redis] get_conversation error: {e}")
        return []

    async def save_conversation(self, conversation_id: str, messages: List[Message]) -> bool:
        key = f"conv:{conversation_id}:messages"
        data = json.dumps([m.model_dump() for m in messages])
        try:
            client = self._get_client()
            if client:
                client.setex(key, DEFAULT_TTL, data)
            else:
                self._mem_set(key, data)
            await self._register_conversation(conversation_id)
            return True
        except Exception as e:
            logger.error(f"[Redis] save_conversation error: {e}")
            return False

    async def append_message(self, conversation_id: str, message: Message) -> bool:
        messages = await self.get_conversation(conversation_id)
        messages.append(message)
        if len(messages) > 30:
            messages = messages[-30:]
        return await self.save_conversation(conversation_id, messages)

    async def delete_conversation(self, conversation_id: str) -> bool:
        keys = [
            f"conv:{conversation_id}:messages",
            f"conv:{conversation_id}:title",
        ]
        try:
            client = self._get_client()
            if client:
                for k in keys:
                    client.delete(k)
                # Eliminar del índice
                client.lrem("conv:index", 0, conversation_id)
            else:
                for k in keys:
                    self._mem_del(k)
                idx = self._mem_get("conv:index") or []
                if conversation_id in idx:
                    idx.remove(conversation_id)
                    self._mem_set("conv:index", idx)
            return True
        except Exception as e:
            logger.error(f"[Redis] delete_conversation error: {e}")
            return False

    # ── Títulos ─────────────────────────────────────────────────────────

    async def get_conversation_title(self, conversation_id: str) -> Optional[str]:
        key = f"conv:{conversation_id}:title"
        try:
            client = self._get_client()
            if client:
                return client.get(key)
            return self._mem_get(key)
        except Exception:
            return None

    async def set_conversation_title(self, conversation_id: str, title: str) -> bool:
        key = f"conv:{conversation_id}:title"
        try:
            client = self._get_client()
            if client:
                client.setex(key, DEFAULT_TTL, title)
            else:
                self._mem_set(key, title)
            return True
        except Exception:
            return False

    # ── Índice de conversaciones ─────────────────────────────────────────

    async def _register_conversation(self, conversation_id: str):
        """Registra la conversación en el índice global."""
        try:
            client = self._get_client()
            if client:
                # Solo agregar si no existe
                existing = client.lrange("conv:index", 0, -1)
                if conversation_id not in (existing or []):
                    client.lpush("conv:index", conversation_id)
                    client.expire("conv:index", DEFAULT_TTL)
            else:
                idx = self._mem_get("conv:index") or []
                if conversation_id not in idx:
                    idx.insert(0, conversation_id)
                    self._mem_set("conv:index", idx)
        except Exception as e:
            logger.warning(f"[Redis] _register_conversation error: {e}")

    async def list_conversations(self) -> list:
        """Lista todas las conversaciones con resumen."""
        try:
            client = self._get_client()
            if client:
                ids = client.lrange("conv:index", 0, 49) or []
            else:
                ids = self._mem_get("conv:index") or []

            result = []
            for conv_id in ids:
                messages = await self.get_conversation(conv_id)
                if not messages:
                    continue
                title = await self.get_conversation_title(conv_id) or "Nueva conversación"
                last_user_msg = next(
                    (m.content[:80] for m in reversed(messages) if m.role == "user"),
                    ""
                )
                result.append({
                    "id": conv_id,
                    "title": title,
                    "message_count": len(messages),
                    "last_message": last_user_msg,
                })
            return result
        except Exception as e:
            logger.error(f"[Redis] list_conversations error: {e}")
            return []


# Instancia global
cache = RedisCache()
