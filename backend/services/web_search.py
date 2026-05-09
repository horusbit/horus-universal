"""
Servicio de búsqueda web en tiempo real — HORUS Universal
Prioridad: Brave Search API > DuckDuckGo library > DuckDuckGo Instant API
"""
import re
import logging
import asyncio
import urllib.parse
from typing import List, Dict

logger = logging.getLogger(__name__)

# Patrones que activan búsqueda web automática
SEARCH_PATTERNS = [
    r'\b(cartelera|cine|pel[ií]cula|horario|caribbean|cinema|movie)\b',
    r'\b(precio|cotizaci[oó]n|d[oó]lar|euro|crypto|bitcoin|ethereum|cuánto cuesta|costo)\b',
    r'\b(noticias?|news|actualidad|[uú]ltimo|reciente|breaking|trending)\b',
    r'\b(hoy|ahora|esta semana|este mes|actual|vigente|en vivo|live|2025|2026)\b',
    r'\b(restaurante|hotel|lugar|abierto|cierra|direcci[oó]n|horario de)\b',
    r'\b(tiempo|clima|temperatura|lluvia|pron[oó]stico|weather)\b',
    r'\b(evento|concierto|festival|partido|juego|torneo|show)\b',
    r'\b(qui[eé]n es|presidente|ceo|director|gobernador|alcalde)\b',
    r'\b(c[oó]mo llegar|ruta|ubicaci[oó]n|cerca de|d[oó]nde queda)\b',
    r'\b(lanzamiento|estreno|nuevo modelo|release|disponible)\b',
    r'\b(busca|encuentra|d[oó]nde puedo|qu[eé] hay|qu[eé] opciones)\b',
    r'\b(cu[aá]l es la|qu[eé] pas[oó]|qu[eé] est[aá] pasando)\b',
]

def needs_web_search(message: str) -> bool:
    msg_lower = message.lower()
    for pattern in SEARCH_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return True
    return False


async def search_web(query: str, max_results: int = 6) -> List[Dict]:
    """Búsqueda con Brave API (primario) → DDGS (secundario) → DDG Instant (terciario)."""
    # 1. Brave Search (más confiable, 2000/mes gratis)
    results = await _search_brave(query, max_results)
    if results:
        return results

    # 2. duckduckgo_search library
    results = await _search_ddgs(query, max_results)
    if results:
        return results

    # 3. DuckDuckGo Instant Answer API
    results = await _search_ddg_instant(query)
    if results:
        return results

    logger.warning(f"[WebSearch] Sin resultados para: {query[:60]}")
    return []


async def _search_brave(query: str, max_results: int) -> List[Dict]:
    """Brave Search API — https://api.search.brave.com"""
    try:
        from config import settings
        api_key = settings.BRAVE_SEARCH_API_KEY
        if not api_key:
            return []

        import aiohttp
        params = {
            "q": query,
            "count": max_results,
            "search_lang": "es",
            "country": "DO",       # República Dominicana como país base
            "safesearch": "off",
            "freshness": "pw",     # past week — resultados frescos
        }
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        url = "https://api.search.brave.com/res/v1/web/search"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[Brave] HTTP {resp.status}")
                    return []
                data = await resp.json()

        results = []
        for item in data.get("web", {}).get("results", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "body": item.get("description", ""),
                "href": item.get("url", ""),
                "source": "brave",
            })

        # También incluir noticias si hay
        for item in data.get("news", {}).get("results", [])[:2]:
            results.append({
                "title": item.get("title", ""),
                "body": item.get("description", ""),
                "href": item.get("url", ""),
                "source": "brave_news",
            })

        if results:
            logger.info(f"[Brave] '{query[:50]}' → {len(results)} resultados")
        return results

    except Exception as e:
        logger.warning(f"[Brave] Error: {e}")
        return []


async def _search_ddgs(query: str, max_results: int) -> List[Dict]:
    """Fallback: librería duckduckgo_search."""
    try:
        from duckduckgo_search import DDGS
        loop = asyncio.get_event_loop()

        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(
                    query, max_results=max_results,
                    region='es-419', safesearch='off',
                ))

        results = await asyncio.wait_for(
            loop.run_in_executor(None, _search),
            timeout=10.0
        )
        if results:
            logger.info(f"[DDGS] '{query[:50]}' → {len(results)} resultados")
        return results or []
    except Exception as e:
        logger.warning(f"[DDGS] Error: {e}")
        return []


async def _search_ddg_instant(query: str) -> List[Dict]:
    """Fallback: DuckDuckGo Instant Answer API (sin clave)."""
    try:
        import aiohttp
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                data = await resp.json(content_type=None)

        results = []
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "body": data["AbstractText"],
                "href": data.get("AbstractURL", ""),
            })
        for topic in data.get("RelatedTopics", [])[:4]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "body": topic.get("Text", ""),
                    "href": topic.get("FirstURL", ""),
                })
        if results:
            logger.info(f"[DDG Instant] '{query[:50]}' → {len(results)} resultados")
        return results
    except Exception as e:
        logger.warning(f"[DDG Instant] Error: {e}")
        return []


def format_search_context(results: List[Dict], query: str) -> str:
    """Formatea resultados como contexto para el LLM."""
    if not results:
        return ""
    lines = [
        f"[🔍 BÚSQUEDA WEB EN TIEMPO REAL — '{query}']",
        "Información encontrada en internet ahora mismo:\n"
    ]
    for i, r in enumerate(results[:5], 1):
        title = r.get('title', '')[:120]
        body  = (r.get('body') or r.get('snippet') or '')[:500]
        href  = r.get('href') or r.get('url', '')
        if body:
            lines.append(f"**Fuente {i}: {title}**")
            lines.append(body)
            if href:
                lines.append(f"🔗 {href}\n")
    lines.append("\n[Responde usando esta información actual. Indica que consultaste internet. Si los datos son insuficientes, dilo.]")
    return "\n".join(lines)
