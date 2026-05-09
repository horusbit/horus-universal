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
        r'\b(código|code|cód|script|función|function|api|backend|frontend|bug|debug|error|python|javascript|js|typescript|ts|react|nextjs|next\.js|fastapi|django|flask|node|sql|database|db|dockerfile|docker|git|github|deploy|endpoint|clase|class|algoritmo|algorithm|regex|json|html|css|scss|devops|servidor|server|autenticación|auth|jwt|webhook|microservicio|arquitectura de software|refactoriza|optimiza el código|implementa|crea una app|crea un script|desarrolla|programa|build|compilar|integración|librería|framework|módulo|package|npm|pip|bash|linux|cli|terminal|lambda|aws|gcp|azure|kubernetes|ci\/cd|testing|unit test|e2e)\b',
    ]),
    (AgentType.NOVA, [
        r'\b(marketing|post|linkedin|instagram|twitter|tiktok|facebook|email|newsletter|campaña|campaign|copy|copywriting|slogan|tagline|branding|anuncio|ad|publicidad|contenido|seo|keyword|viral|engagement|redacta|escribe un email|crea contenido|marca|identidad de marca|propuesta de valor|mensaje de marketing|estrategia de contenido|blog|artículo de marketing|landing page|página de aterrizaje)\b',
    ]),
    (AgentType.LEXIS, [
        r'\b(contrato|contract|legal|abogado|lawyer|nda|confidencialidad|términos de servicio|política de privacidad|gdpr|compliance|cláusula|clause|acuerdo|agreement|licencia|license|copyright|marca registrada|trademark|propiedad intelectual|constitución de empresa|estatutos|redacta un contrato|revisa este documento|aspecto legal|implicaciones legales|es legal|legalmente)\b',
    ]),
    (AgentType.ORACLE, [
        r'\b(negocio|business|estrategia|strategy|startup|inversión|investment|financiero|financial|revenue|modelo de negocio|business model|mercado|market|competencia|competitor|kpi|métrica|metric|pitch|fundraising|valuation|swot|foda|okr|escalar|crecer la empresa|análisis de negocio|plan de negocio|modelo de ingresos|rentabilidad|margen|flujo de caja|proyección|forecast|due diligence|venture|capital de riesgo|bootstrapping|product market fit|go to market)\b',
    ]),
    (AgentType.HERMES, [
        r'\b(traduce|translate|traducción|translation|en inglés|en español|en francés|en alemán|en portugués|en italiano|en chino|en japonés|en árabe|en ruso|to english|to spanish|al inglés|al español|al francés|localización|localization|idioma|language|multilingual|subtitular)\b',
    ]),
    (AgentType.DARWIN, [
        r'\b(investiga|research|análisis profundo|analiza|datos estadísticos|estadística|statistic|tendencia|trend|comparativa|benchmark|paper|estudio científico|informe|fact.check|dame información sobre|necesito saber sobre|tendencias en|qué dicen los estudios|evidencia|fuentes|cita|referencia|contexto histórico|evolución de|estado actual de)\b',
    ]),
    (AgentType.PIXEL, [
        r'\b(imagen|image|foto|photo|diseño gráfico|midjourney|dall-e|stable diffusion|flux|prompt de imagen|visual|ilustración|illustration|logo|ícono|icon|arte digital|estilo visual|paleta de color|genera una imagen|crea un prompt|diseña un logo|prompt para imagen|render|mockup|ui design|ux design|interfaz visual|prototipo visual)\b',
    ]),
    (AgentType.ECHO, [
        r'\b(podcast|audio|voz|voice|guión|locutor|narración|narration|tts|text.to.speech|subtítulo|subtitle|transcribe|transcripción|grabación|recording|video script|youtube script|escribe un guión|crea un podcast|para grabar|para audio|intro de podcast|episodio|libreto|radio)\b',
    ]),
    (AgentType.NEXUS, [
        r'\b(redes sociales|social media|instagram|tiktok|twitter|x\.com|linkedin|youtube|facebook|threads|pinterest|reels|stories|hashtag|influencer|growth hacking|community manager|followers|seguidores|contenido viral|estrategia de redes|calendario de contenido|crecer en|aumentar seguidores|post para|publicar en|algoritmo de instagram|algoritmo de tiktok|personal brand|marca personal en redes)\b',
    ]),
    (AgentType.FORGE, [
        r'\b(excel|google sheets|spreadsheet|hoja de cálculo|tableau|power bi|looker|pandas|numpy|dataframe|pivot|vlookup|buscarv|fórmula de excel|dashboard de datos|gráfico de datos|chart|sql query|business intelligence|bi|limpieza de datos|analiza estos datos|crea un dashboard|dame una fórmula|analiza el excel|tabla dinámica|visualiza los datos|csv|etl|data pipeline|métricas de negocio|reporte de ventas|kpi dashboard)\b',
    ]),
    (AgentType.SAGE, [
        r'\b(explícame cómo|enséñame|quiero aprender|tutorial paso a paso|curso de|lección|examen|tarea escolar|matemáticas|física|química|biología|historia|geografía|filosofía|gramática|aprendizaje|conceptos básicos de|para principiantes|no entiendo|ayúdame a entender|qué significa|definición de|cómo se hace|guía completa de)\b',
    ]),
    (AgentType.VECTOR, [
        r'\b(ventas|sales|crm|pipeline|prospecto|prospect|lead|cold call|cold email|objeción de ventas|cierre de venta|negociación comercial|deal|hubspot|salesforce|pipedrive|upsell|cross.sell|funnel de ventas|conversión de ventas|script de ventas|cómo vender|manejo de objeciones|cerrar un trato|email de ventas|propuesta comercial|comisión|quota|b2b sales|b2c sales)\b',
    ]),
    (AgentType.CHRONOS, [
        r'\b(productividad|organización personal|planificación|gestión del tiempo|time management|agenda|prioridades|gtd|pomodoro|hábitos|rutina diaria|automatización de tareas|workflow|notion|trello|asana|monday|clickup|todoist|burnout|delegación|sistema de trabajo|organiza mi semana|planifica mi día|crea un plan de trabajo|cómo ser más productivo|gestión de proyectos)\b',
    ]),
    (AgentType.POLITEIA, [
        r'\b(política|político|gobierno|gobernanza|campaña electoral|elecciones|candidato|partido político|congreso|parlamento|senado|presidente|alcalde|legislación|política pública|votantes|electorado|geopolítica|diplomacia|estrategia política|comunicación política|discurso político|plan de gobierno|política exterior|reforma)\b',
    ]),
    (AgentType.EDUCRAFT, [
        r'\b(plataforma educativa|lms|curso online|curso virtual|e-learning|elearning|moodle|teachable|thinkific|kajabi|coursera|edx|udemy|platzi|masterclass|diseño instruccional|syllabus|curriculum virtual|certificado online|aula virtual|crea un curso|diseña una plataforma educativa|landing page de curso|escuela online|membresía educativa|academia virtual)\b',
    ]),
]


def detect_agent(message: str, requested_agent=None) -> AgentType:
    """
    Detecta el agente más apropiado para manejar el mensaje.
    Si el usuario ya eligió un agente específico (no ATLAS), respeta esa elección.
    """
    # Si el usuario eligió un agente específico, respetarlo
    if requested_agent and requested_agent != AgentType.ATLAS:
        # Solo respetar si es un AgentType válido (no UUID de custom agent)
        if isinstance(requested_agent, AgentType):
            return requested_agent

    msg_lower = message.lower()

    # Buscar coincidencias por agente
    scores = {}
    for agent_type, patterns in ROUTING_RULES:
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, msg_lower, re.IGNORECASE)
            score += len(matches) * 2  # peso doble por match
        if score > 0:
            scores[agent_type] = score

    if not scores:
        return AgentType.ATLAS  # Sin coincidencias claras → ATLAS responde

    best_agent = max(scores, key=scores.get)
    logger.info(f"[Router] '{message[:60]}' → {best_agent.value} (scores={dict(sorted(scores.items(), key=lambda x: -x[1])[:3])})")
    return best_agent


def get_routing_message(detected_agent: AgentType, original_agent) -> str | None:
    """Retorna mensaje de routing si se cambió de agente."""
    if detected_agent != original_agent and original_agent == AgentType.ATLAS:
        agent_names = {
            AgentType.CIPHER:   "CIPHER ⚡",
            AgentType.NOVA:     "NOVA ✨",
            AgentType.LEXIS:    "LEXIS ⚖️",
            AgentType.ORACLE:   "ORACLE 🔮",
            AgentType.HERMES:   "HERMES 🌍",
            AgentType.ECHO:     "ECHO 🎙️",
            AgentType.DARWIN:   "DARWIN 🔬",
            AgentType.PIXEL:    "PIXEL 🎨",
            AgentType.NEXUS:    "NEXUS 📡",
            AgentType.FORGE:    "FORGE 📊",
            AgentType.SAGE:     "SAGE 🎓",
            AgentType.VECTOR:   "VECTOR 💼",
            AgentType.CHRONOS:  "CHRONOS ⏱️",
            AgentType.POLITEIA: "POLITEIA 🏛️",
            AgentType.EDUCRAFT: "EDUCRAFT 🏫",
        }
        name = agent_names.get(detected_agent, detected_agent.value.upper())
        return f"*Activando {name}...*\n\n"
    return None
