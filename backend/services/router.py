"""
Servicio de auto-routing inteligente para HORUS Universal.
Detecta qué agente debe manejar una solicitud basándose en el contenido.
"""
import re
from models.schemas import AgentType, Message
import logging

logger = logging.getLogger(__name__)

# Palabras clave por agente — orden importa (más específico primero)
ROUTING_RULES = [
    (AgentType.CIPHER, [
        r'\b(código|code|script|función|function|api|backend|frontend|bug|debug|error|python|javascript|typescript|react|nextjs|fastapi|django|sql|database|dockerfile|git|github|deploy|endpoint|clase|class|algoritmo|algorithm|regex|json|html|css)\b',
        r'\b(programa|programa|desarrolla|crea una app|crea un script|implementa|refactoriza|optimiza el código)\b',
    ]),
    (AgentType.NOVA, [
        r'\b(marketing|post|linkedin|instagram|twitter|tiktok|facebook|email|newsletter|campaña|campaign|copy|copywriting|slogan|tagline|branding|anuncio|ad|publicidad|contenido|content|seo|keyword|viral|engagement)\b',
        r'\b(redacta un post|escribe un email|crea contenido|estrategia de contenido|calendario editorial)\b',
    ]),
    (AgentType.LEXIS, [
        r'\b(contrato|contract|legal|abogado|lawyer|nda|confidencialidad|términos de servicio|política de privacidad|gdpr|compliance|cláusula|clause|acuerdo|agreement|licencia|license|copyright|marca registrada|trademark)\b',
        r'\b(redacta un contrato|revisa este documento legal|análisis legal|aspecto legal)\b',
    ]),
    (AgentType.ORACLE, [
        r'\b(negocio|business|estrategia|strategy|startup|inversión|investment|financiero|financial|revenue|modelo de negocio|business model|mercado|market|competencia|competitor|kpi|métrica|metric|pitch|fundraising|valuation|swot|foda|okr)\b',
        r'\b(análisis de negocio|plan de negocio|cómo escalar|cómo crecer|modelo de ingresos)\b',
    ]),
    (AgentType.HERMES, [
        r'\b(traduce|translate|traducción|translation|en inglés|en español|en francés|en alemán|en portugués|en italiano|en chino|en japonés|en árabe|to english|to spanish|al inglés|al español)\b',
        r'\b(localización|localization|idioma|language)\b',
    ]),
    (AgentType.DARWIN, [
        r'\b(investiga|research|análisis|analyze|datos|data|estadística|statistic|tendencia|trend|comparativa|comparación|benchmark|paper|estudio|study|informe|report|fact.check|qué es|cómo funciona|explica|explícame)\b',
        r'\b(profundiza|dame información sobre|necesito saber sobre|tendencias en)\b',
    ]),
    (AgentType.PIXEL, [
        r'\b(imagen|image|foto|photo|diseño|design|midjourney|dall-e|stable diffusion|flux|prompt de imagen|visual|ilustración|illustration|logo|ícono|icon|arte|art|estilo visual|paleta de color)\b',
        r'\b(genera una imagen|crea un prompt|diseña|ilustra|prompt para)\b',
    ]),
    (AgentType.ECHO, [
        r'\b(podcast|audio|voz|voice|script|guión|locutor|narración|narration|tts|text.to.speech|subtítulo|subtitle|transcribe|transcripción|grabación|recording|video script|youtube script)\b',
        r'\b(escribe un guión|crea un podcast|para grabar|para audio)\b',
    ]),
]


def detect_agent(message: str, requested_agent: AgentType = AgentType.ATLAS) -> AgentType:
    """
    Detecta el agente más apropiado para manejar el mensaje.
    Si el usuario ya eligió un agente específico (no ATLAS), respeta esa elección.
    """
    # Si el usuario eligió un agente específico, respetarlo
    if requested_agent != AgentType.ATLAS:
        return requested_agent

    msg_lower = message.lower()

    # Buscar coincidencias por agente
    scores = {}
    for agent_type, patterns in ROUTING_RULES:
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, msg_lower, re.IGNORECASE)
            score += len(matches)
        if score > 0:
            scores[agent_type] = score

    if not scores:
        return AgentType.ATLAS  # Sin coincidencias claras → ATLAS responde

    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]

    logger.info(f"[Router] Auto-routing: '{message[:50]}...' → {best_agent.value} (score={best_score})")
    return best_agent


def get_routing_message(detected_agent: AgentType, original_agent: AgentType) -> str | None:
    """Retorna mensaje de routing si se cambió de agente."""
    if detected_agent != original_agent and original_agent == AgentType.ATLAS:
        agent_names = {
            AgentType.CIPHER: "CIPHER ⚡",
            AgentType.NOVA: "NOVA ✨",
            AgentType.LEXIS: "LEXIS ⚖️",
            AgentType.ORACLE: "ORACLE 🔮",
            AgentType.HERMES: "HERMES 🌍",
            AgentType.ECHO: "ECHO 🎙️",
            AgentType.DARWIN: "DARWIN 🔬",
            AgentType.PIXEL: "PIXEL 🎨",
        }
        name = agent_names.get(detected_agent, detected_agent.value.upper())
        return f"*Activando agente {name}...*\n\n"
    return None
