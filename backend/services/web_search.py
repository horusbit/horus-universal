"""
Servicio de búsqueda web en tiempo real — HORUS Universal
Prioridad: Tavily API > DuckDuckGo library > DuckDuckGo Instant API
Tavily está diseñado específicamente para agentes de IA.
"""
import re
import logging
import asyncio
import urllib.parse
from typing import List, Dict

logger = logging.getLogger(__name__)

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
    """Tavily (primario) → DDGS (secundario) → DDG Instant (terciario)."""
    results = await _search_tavily(query, max_results)
    if results:
        return results

    results = await _search_ddgs(query, max_results)
    if results:
        return results

    results = await _search_ddg_instant(query)
    if results:
        return results

    # 4. HTML scraping fallback (no API key, works anywhere)
    results = await _search_html_scrape(query)
    if results:
        return results

    logger.warning(f"[WebSearch] Sin resultados para: {query[:60]}")
    return []


async def _search_tavily(query: str, max_results: int) -> List[Dict]:
    """Tavily Search API — diseñada para agentes IA. 1000/mes gratis."""
    try:
        from config import settings
        api_key = getattr(settings, 'TAVILY_API_KEY', '') or getattr(settings, 'BRAVE_SEARCH_API_KEY', '')
        if not api_key:
            return []

        import aiohttp
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "include_raw_content": False,
            "max_results": max_results,
            "include_domains": [],
            "exclude_domains": [],
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[Tavily] HTTP {resp.status}")
                    return []
                data = await resp.json()

        results = []
        # Respuesta directa de Tavily (muy útil)
        if data.get("answer"):
            results.append({
                "title": f"Respuesta directa: {query[:60]}",
                "body": data["answer"],
                "href": "",
                "source": "tavily_answer",
            })
        # Resultados web
        for item in data.get("results", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "body": item.get("content", "")[:500],
                "href": item.get("url", ""),
                "source": "tavily",
            })

        if results:
            logger.info(f"[Tavily] '{query[:50]}' → {len(results)} resultados")
        return results

    except Exception as e:
        logger.warning(f"[Tavily] Error: {e}")
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


async def _search_html_scrape(query: str) -> List[Dict]:
    """Fallback final: scraping directo de DuckDuckGo HTML. Sin API key."""
    try:
        import aiohttp
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self._in_result = False
                self._current = {}
                self._capture = None

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'a' and 'result__a' in attrs.get('class', ''):
                    self._current = {'href': attrs.get('href', '')}
                    self._capture = 'title'
                elif tag == 'a' and 'result__snippet' in attrs.get('class', ''):
                    self._capture = 'body'

            def handle_data(self, data):
                if self._capture and data.strip():
                    self._current[self._capture] = (self._current.get(self._capture, '') + data).strip()

            def handle_endtag(self, tag):
                if tag == 'a' and self._capture == 'title' and self._current.get('title'):
                    self.results.append(dict(self._current))
                    self._capture = None
                elif tag == 'a' and self._capture == 'body':
                    self._capture = None

        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}&kl=es-419"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            "Accept-Language": "es-419,es;q=0.9",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

        parser = DDGParser()
        parser.feed(html)
        results = [r for r in parser.results if r.get('title') and r.get('href')][:6]
        if results:
            logger.info(f"[DDG Scrape] '{query[:50]}' → {len(results)} resultados")
        return results
    except Exception as e:
        logger.warning(f"[DDG Scrape] Error: {e}")
        return []


def format_search_context(results: List[Dict], query: str) -> str:
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
    lines.append("\n[Responde usando esta información actual. Indica que consultaste internet.]")
    return "\n".join(lines)
