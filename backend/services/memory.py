"""
Servicio de Memoria de Usuario — HORUS Universal
Recuerda hechos clave del usuario entre sesiones y chats.
Se inyecta en el system prompt de todos los agentes.
"""
import re
from config import settings
import logging

logger = logging.getLogger(__name__)

# Patrones para extraer hechos automáticamente de los mensajes
MEMORY_PATTERNS = [
    (r"me llamo\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)", "nombre"),
    (r"mi nombre es\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)", "nombre"),
    (r"soy\s+(desarrollador|diseñador|emprendedor|médico|abogado|ingeniero|consultor|estudiante|profesor|periodista|marketero|contador|arquitecto|psicólogo|vendedor)", "profesion"),
    (r"trabajo (?:en|como)\s+([^.,\n]{3,40})", "trabajo"),
    (r"mi empresa (?:es|se llama)\s+([^.,\n]{2,50})", "empresa"),
    (r"vivo en\s+([^.,\n]{3,40})", "ubicacion"),
    (r"soy de\s+([^.,\n]{3,40})", "ubicacion"),
    (r"hablo\s+(inglés|español|francés|alemán|portugués|italiano|chino|japonés|árabe)", "idioma"),
    (r"prefiero (?:que me hables en|respuestas en)\s+([^.,\n]{3,30})", "idioma_preferido"),
    (r"mi (?:proyecto|startup|app|producto|servicio) (?:es|se llama)\s+([^.,\n]{2,50})", "proyecto"),
]


def _get_client():
    from supabase import create_client
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    )


async def get_user_memory(user_id: str) -> dict:
    """Devuelve todos los hechos recordados del usuario."""
    try:
        client = _get_client()
        result = client.table("user_memory") \
            .select("key, value") \
            .eq("user_id", user_id) \
            .limit(20) \
            .execute()
        return {row["key"]: row["value"] for row in (result.data or [])}
    except Exception as e:
        logger.warning(f"[Memory] get_user_memory error: {e}")
        return {}


async def save_memory_fact(user_id: str, key: str, value: str, source: str = "auto") -> bool:
    """Guarda o actualiza un hecho del usuario."""
    try:
        client = _get_client()
        client.table("user_memory").upsert({
            "user_id": user_id,
            "key": key,
            "value": value[:500],
            "source": source,
        }, on_conflict="user_id,key").execute()
        return True
    except Exception as e:
        logger.warning(f"[Memory] save_memory_fact error: {e}")
        return False


async def extract_and_save_facts(user_id: str, user_message: str) -> int:
    """
    Extrae hechos del mensaje del usuario y los guarda.
    Devuelve el número de hechos nuevos guardados.
    """
    msg_lower = user_message.lower()
    saved = 0
    for pattern, key in MEMORY_PATTERNS:
        match = re.search(pattern, msg_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip().title()
            if value and len(value) > 1:
                await save_memory_fact(user_id, key, value, source="auto")
                saved += 1
                logger.debug(f"[Memory] Auto-saved: {key}={value} for user {user_id[:8]}...")
    return saved


async def delete_memory_fact(user_id: str, key: str) -> bool:
    """Elimina un hecho específico de la memoria del usuario."""
    try:
        client = _get_client()
        client.table("user_memory") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("key", key) \
            .execute()
        return True
    except Exception as e:
        logger.warning(f"[Memory] delete_memory_fact error: {e}")
        return False


async def clear_user_memory(user_id: str) -> bool:
    """Borra toda la memoria del usuario."""
    try:
        client = _get_client()
        client.table("user_memory").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        logger.warning(f"[Memory] clear_user_memory error: {e}")
        return False


def build_memory_context(memory: dict) -> str:
    """Construye el bloque de contexto de memoria para inyectar en system prompts."""
    if not memory:
        return ""

    KEY_LABELS = {
        "nombre": "Nombre",
        "profesion": "Profesión",
        "trabajo": "Trabaja en",
        "empresa": "Empresa",
        "ubicacion": "Ubicación",
        "idioma": "Idioma",
        "idioma_preferido": "Idioma preferido",
        "proyecto": "Proyecto actual",
    }

    lines = []
    for key, value in memory.items():
        label = KEY_LABELS.get(key, key.capitalize())
        lines.append(f"- {label}: {value}")

    if not lines:
        return ""

    return f"\n\n## Información recordada del usuario\n" + "\n".join(lines) + "\n"
