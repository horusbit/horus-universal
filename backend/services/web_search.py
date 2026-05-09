"""
Servicio de búsqueda web — DuckDuckGo + fallback HTTP.
Búsqueda real en tiempo real para dar contexto actualizado a los agentes.
"""
import re
import logging
import asyncio
import urllib.parse
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

# Patrones que SIEMPRE activan búsqueda web
SEARCH_PATTERNS = [
    # Entretenimiento / cine
    r'\b(cartelera|cine|pel[ií]cula|horario|cines|caribbean|cinema|movies?)\b',
    # Precios / finanzas
    r'\b(precio|cotizaci[oó]n|d[oó]lar|euro|crypto|bitcoin|ethereum|costo|cuánto cuesta)\b',
    # Noticias
    r'\b(noticias?|news|actualidad|[uú]ltimo|reciente|breaking)\b',
    # Tiempo / fecha actual
    r'\b(hoy|ahora|esta semana|este mes|actual|vigente|en vivo|live|2024|2025|2026)\b',
    # Lugares / negocios
    r'\b(restaurante|hotel|lugar|d[oó]nde|abierto|cierra|direcci[oó]n|horario de)\b',
    # Clima
    r'\b(tiempo|clima|temperatura|lluvia|pron[oó]stico|weather)\b',
    # Eventos
    r'\b(evento|concierto|festival|partido|juego|torneo|show)\b',
    # Personas / quién es
    r'\b(qui[eé]n es|qui[eé]nes son|cu[aá]ndo naci[oó]|presidente|ceo|director)\b',
    # Llegar a lugar
    r'\b(c[oó]mo llegar|ruta|mapa|ubicaci[oó]n|cerca de)\b',
    # Lanzamientos
    r'\b(lanzamiento|estreno|nuevo modelo|sale|release|disponible)\b',
    # Buscar / encontrar
    r'\b(busca|encuentra|d[oó]nde puedo|qu[eé] hay|qu[eé] opciones)\b',
    # Preguntas factuales sobre el mundo real
    r'\b(cu[aá]l es la|cu[aá]les son los|qu[eé] pas[oó]|qu[eé] est[aá] pasando)\b',
]

def needs_web_search(message: str) -> bool:
    """Detecta si el mensaje requiere búsqueda web en tiempo real."""
    msg_lower = message.lower()
    for pattern in SEARCH_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return True
    return False


async def search_web(query: str, max_results: int = 6) -> List[Dict]:
    """
    Búsqueda web con DuckDuckGo. Intenta librería primero, luego API HTTP.
    Retorna lista de resultados con title, body, href.
    """
    # Método 1: librería duckduckgo_search
    results = await _search_ddgs(query, max_results)
    if results:
        return results

    # Método 2: DuckDuckGo Instant Answer API (sin clave)
    results = await _search_ddg_api(query)
    if results:
        return results

    logger.warning(f"[WebSearch] No se obtuvieron resultados para: {query[:60]}")
    return []


async def _search_ddgs(query: str, max_results: int) -> List[Dict]:
    """Búsqueda con librería duckduckgo_search."""
    try:
        from duckduckgo_search import DDGS
        loop = asyncio.get_event_loop()

        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(
                    query,
                    max_results=max_results,
                    region='es-419',
                    safesearch='off',
                ))

        results = await asyncio.wait_for(
            loop.run_in_executor(None, _search),
            timeout=10.0
        )
        if results:
            logger.info(f"[WebSearch DDGS] '{query[:50]}' → {len(results)} resultados")
        return results or []
    except asyncio.TimeoutError:
        logger.warning("[WebSearch DDGS] Timeout")
        return []
    except ImportError:
        logger.warning("[WebSearch DDGS] librería no instalada")
        return []
    except Exception as e:
        logger.warning(f"[WebSearch DDGS] Error: {e}")
        return []


async def _search_ddg_api(query: str) -> List[Dict]:
    """Fallback: DuckDuckGo Instant Answer API."""
    try:
        import aiohttp
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                data = await resp.json(content_type=None)

        results = []
        # Abstract (respuesta directa)
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "body": data["AbstractText"],
                "href": data.get("AbstractURL", ""),
            })
        # Related topics
        for topic in data.get("RelatedTopics", [])[:4]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "body": topic.get("Text", ""),
                    "href": topic.get("FirstURL", ""),
                })
        if results:
            logger.info(f"[WebSearch API] '{query[:50]}' → {len(results)} resultados")
        return results
    except Exception as e:
        logger.warning(f"[WebSearch API] Error: {e}")
        return []


def format_search_context(results: List[Dict], query: str) -> str:
    """Formatea resultados como contexto para el LLM."""
    if not results:
        return ""
    lines = [
        f"[🔍 BÚSQUEDA WEB EN TIEMPO REAL para: '{query}']",
        "Información encontrada en internet ahora mismo:\n"
    ]
    for i, r in enumerate(results[:5], 1):
        title = r.get('title', 'Sin título')[:100]
        body = (r.get('body') or r.get('snippet') or r.get('AbstractText') or '')[:500]
        url = r.get('href') or r.get('url', '')
        if body:
            lines.append(f"**Fuente {i}: {title}**")
            lines.append(f"{body}")
            if url:
                lines.append(f"🔗 {url}\n")
    lines.append("\n[INSTRUCCIÓN: Usa esta información real para responder. Menciona que buscaste en internet. Si hay información específica sobre lo que preguntó el usuario, úsala. Si los resultados no son suficientes, dilo claramente.]")
    return "\n".join(lines)
