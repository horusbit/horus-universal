"""
Servicio de búsqueda web gratuita — DuckDuckGo, sin API key.
Se usa para dar contexto actual a los agentes cuando el usuario
pregunta sobre información en tiempo real.
"""
import re
import logging
import asyncio
from typing import List, Dict

logger = logging.getLogger(__name__)

# Palabras que indican necesidad de búsqueda web
SEARCH_PATTERNS = [
    r'\b(cartelera|cine|película|pelicula|horario|cines)\b',
    r'\b(precio|cotización|cotizacion|dólar|euro|crypto|bitcoin)\b',
    r'\b(noticias|noticia|news|actualidad|último|ultima|reciente)\b',
    r'\b(hoy|ahora|esta semana|este mes|actual|vigente|en vivo)\b',
    r'\b(restaurante|hotel|lugar|dónde|donde queda|abierto|cierra)\b',
    r'\b(tiempo|clima|temperatura|lluvia|pronóstico)\b',
    r'\b(evento|concierto|festival|partido|juego)\b',
    r'\b(quién es|quien es|quiénes son|donde está|dónde está)\b',
    r'\b(cuánto cuesta|cuanto cuesta|cómo llegar|como llegar)\b',
    r'\b(inaugur|lanzamiento|estreno|nuevo|nueva|sale)\b.*\b(hoy|esta semana)\b',
    r'\bhttps?://|www\.',
]

def needs_web_search(message: str) -> bool:
    """Detecta si el mensaje requiere búsqueda web."""
    msg_lower = message.lower()
    for pattern in SEARCH_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return True
    return False

async def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """Búsqueda web con DuckDuckGo. Retorna lista de resultados."""
    try:
        from duckduckgo_search import DDGS
        loop = asyncio.get_event_loop()
        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(
                    query,
                    max_results=max_results,
                    region='es-419',   # Español Latinoamérica
                    safesearch='off',
                ))
        results = await loop.run_in_executor(None, _search)
        logger.info(f"[WebSearch] '{query[:50]}' → {len(results)} resultados")
        return results or []
    except ImportError:
        logger.warning("[WebSearch] duckduckgo_search no instalado. Agrega al requirements.txt")
        return []
    except Exception as e:
        logger.warning(f"[WebSearch] Error: {e}")
        return []

def format_search_context(results: List[Dict], query: str) -> str:
    """Formatea resultados como contexto para el LLM."""
    if not results:
        return ""
    lines = [
        f"[🔍 BÚSQUEDA WEB para: '{query}']",
        "Información encontrada en internet (usa estos datos para responder):\n"
    ]
    for i, r in enumerate(results[:4], 1):
        title = r.get('title', 'Sin título')
        body = (r.get('body') or r.get('snippet') or '')[:400]
        url = r.get('href') or r.get('url', '')
        if body:
            lines.append(f"**Fuente {i}: {title}**")
            lines.append(f"{body}")
            if url:
                lines.append(f"🔗 {url}\n")
    lines.append("[Responde basándote en esta información actualizada. Menciona las fuentes.]")
    return "\n".join(lines)
