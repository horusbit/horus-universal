from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

# Clean BOM from python files
for p in (root / "backend").rglob("*.py"):
    txt = p.read_text(encoding="utf-8-sig").replace("\ufeff", "")
    p.write_text(txt, encoding="utf-8")

# Global quality prompt
quality_prompt = r'''
HORUS_GLOBAL_QUALITY_PROMPT = """
You are HORUS, a premium AI operating system with specialized agents.

Global behavior:
- Deliver final usable products, not only explanations.
- Be concise, natural, warm and practical.
- Think like ChatGPT, Claude and Gemini: helpful, direct, intelligent and polished.
- Always improve the user's request internally before answering.
- Produce the best possible quality using free/open tools first.
- If a task needs a visual, create visible image links and previews.
- If a task needs code, deliver clean working code.
- If a task needs legal/business/marketing output, deliver professional documents, structure and next steps.
- If a task needs research, be clear about limits and cite or mention sources when available.
- Never sound robotic or generic.
- Never say "I cannot" when a useful workaround exists.
- Avoid long filler. Give the result first, explanation second.
- Match the user's language.

Quality standard:
1. Understand the real goal.
2. Route to the best agent.
3. Produce a finished deliverable.
4. Include improvements or variations when useful.
5. Keep responses elegant, short and useful.

Visual standard:
For logos, images, architecture, mockups, UI, posters, flyers, branding, renders or visual concepts:
- Generate Pollinations Flux image URLs.
- Use markdown image syntax.
- Provide 2 or 3 variations when possible.
- Use professional prompt enhancement.
- Never only give Canva/Midjourney instructions.
"""
'''

# Upgrade visual service
visual_service = root / "backend/services/visual_service.py"
visual_service.parent.mkdir(parents=True, exist_ok=True)
visual_service.write_text(r'''
from urllib.parse import quote
import hashlib

VISUAL_WORDS = [
    "logo", "imagen", "image", "render", "mockup", "branding",
    "diseno", "diseño", "arquitectura", "plano", "casa",
    "poster", "flyer", "banner", "ui", "app", "web", "visual",
    "interior", "fachada", "ingenieria", "engineering", "foto",
    "arte", "ilustracion", "ilustración", "dibujo"
]

def is_visual_request(text: str) -> bool:
    if not text:
        return False
    return any(w in text.lower() for w in VISUAL_WORDS)

def enhance_visual_prompt(prompt: str) -> str:
    p = prompt.strip()
    low = p.lower()

    quality = (
        "masterpiece quality, premium professional design, clean composition, "
        "sharp details, balanced symmetry, refined proportions, polished final result, "
        "high-end commercial quality, no watermark, no blur, no distortion"
    )

    if any(w in low for w in ["logo", "branding", "marca"]):
        return (
            f"Luxury professional logo concept for: {p}. "
            "Minimalist corporate identity, custom vector-style symbol, refined negative space, "
            "premium typography direction, elegant geometric construction, clean iconic mark, "
            "high-end law firm and international consulting brand aesthetic, balanced layout, "
            "deep navy, graphite gray, red accents or metallic gold depending on request, "
            "isolated centered composition, no random letters, no clutter, Behance quality, "
            f"{quality}"
        )

    if any(w in low for w in ["arquitectura", "plano", "casa", "edificio", "fachada", "interior"]):
        return (
            f"Professional architectural visualization for: {p}. "
            "Modern realistic architecture render, coherent spatial layout, premium materials, "
            "accurate proportions, cinematic natural light, realistic shadows, presentation board quality, "
            f"{quality}"
        )

    if any(w in low for w in ["app", "web", "ui", "landing", "mockup", "dashboard"]):
        return (
            f"Premium UI/UX product mockup for: {p}. "
            "Modern SaaS interface, clean layout, beautiful spacing, strong visual hierarchy, "
            "responsive web app design, elegant dashboard, polished product presentation, "
            f"{quality}"
        )

    return f"{p}. {quality}"

def make_pollinations_url(prompt: str, variant: int = 1, width: int = 1024, height: int = 1024) -> str:
    enhanced = enhance_visual_prompt(prompt)
    seed = int(hashlib.sha256((prompt + str(variant)).encode("utf-8")).hexdigest()[:8], 16)
    return (
        "https://image.pollinations.ai/prompt/"
        + quote(enhanced)
        + f"?width={width}&height={height}&seed={seed}&model=flux&enhance=true&nologo=true"
    )

def make_image_markdown(prompt: str) -> str:
    enhanced = enhance_visual_prompt(prompt)
    urls = [make_pollinations_url(prompt, i) for i in [1, 2, 3]]

    return f"""Te prepare 3 propuestas visuales iniciales con el mejor modo gratuito disponible:

### Opcion 1
![Imagen generada]({urls[0]})

### Opcion 2
![Imagen generada]({urls[1]})

### Opcion 3
![Imagen generada]({urls[2]})

Prompt profesional usado:
{enhanced}

Puedo hacer otra ronda mas premium, minimalista, realista, tecnologica, arquitectonica o corporativa.
"""
''', encoding="utf-8")

# Patch openrouter global prompt
openrouter = root / "backend/services/openrouter.py"
if openrouter.exists():
    txt = openrouter.read_text(encoding="utf-8")
    if "HORUS_GLOBAL_QUALITY_PROMPT" not in txt:
        txt = quality_prompt + "\n" + txt

    # Make sure _normalize_messages injects quality prompt
    if "HORUS_GLOBAL_QUALITY_PROMPT" in txt and "HORUS_QUALITY_INJECTED" not in txt:
        txt = txt.replace(
            "def _normalize_messages(messages):",
            '''# HORUS_QUALITY_INJECTED
def _normalize_messages(messages):'''
        )

        txt = txt.replace(
            "return normalized",
            '''has_system = any(isinstance(m, dict) and m.get("role") == "system" for m in normalized)
    if has_system:
        for m in normalized:
            if isinstance(m, dict) and m.get("role") == "system":
                m["content"] = HORUS_GLOBAL_QUALITY_PROMPT + "\\n\\n" + str(m.get("content", ""))
                break
    else:
        normalized.insert(0, {"role": "system", "content": HORUS_GLOBAL_QUALITY_PROMPT})

    return normalized''',
            1
        )

    openrouter.write_text(txt, encoding="utf-8")

# Upgrade all agents with quality instructions
agent_rules = {
    "atlas.py": "ATLAS routes every task to the best agent and delivers concise final results.",
    "pixel.py": "PIXEL creates visible visual outputs, image links, prompts, previews and design variations.",
    "nova.py": "NOVA delivers high-conversion marketing assets, hooks, captions, ads and campaign ideas.",
    "lexis.py": "LEXIS delivers polished legal drafts, summaries, clauses, risks and action steps.",
    "oracle.py": "ORACLE delivers business strategy, financial logic, decisions, scenarios and execution plans.",
    "cipher.py": "CIPHER delivers clean working code, debugging steps, architecture and deployment guidance.",
    "hermes.py": "HERMES delivers professional translation, localization, tone adaptation and formatting.",
    "darwin.py": "DARWIN delivers research synthesis, trends, comparisons and recommendations.",
    "echo.py": "ECHO delivers voice, scripts, spoken communication and audio-ready text.",
    "nexus.py": "NEXUS delivers automation workflows, integrations and process optimization.",
    "chronos.py": "CHRONOS delivers scheduling, planning, reminders and time management.",
    "forge.py": "FORGE delivers product building, artifacts, prototypes and execution systems.",
    "sage.py": "SAGE delivers education, coaching and clear explanations.",
    "vector.py": "VECTOR delivers memory, retrieval and knowledge organization.",
    "politeia.py": "POLITEIA delivers governance, public policy and institutional analysis.",
    "educraft.py": "EDUCRAFT delivers learning products, courses and training material."
}

agents_dir = root / "backend/agents"
if agents_dir.exists():
    for file, role in agent_rules.items():
        p = agents_dir / file
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            marker = "HORUS_AGENT_QUALITY_RULE"
            block = f'''
HORUS_AGENT_QUALITY_RULE = """
{role}

Universal quality rules:
- Deliver the final useful product first.
- Be concise, warm, human and premium.
- Avoid generic filler.
- Improve the user's request internally.
- Use the best free available method.
- If visual, show image links/previews.
- If code, make it runnable.
- If document, make it professional.
- If strategy, make it actionable.
"""
'''
            if marker not in txt:
                txt = block + "\n" + txt
            p.write_text(txt, encoding="utf-8")

# Patch chat visual intercept if possible
chat = root / "backend/routers/chat.py"
if chat.exists():
    c = chat.read_text(encoding="utf-8")
    if "from services.visual_service import is_visual_request, make_image_markdown" not in c:
        c = c.replace(
            "from agents import get_agent",
            "from agents import get_agent\nfrom services.visual_service import is_visual_request, make_image_markdown"
        )

    # Only add if not already present and if request object likely exists
    if "HORUS VISUAL DIRECT INTERCEPT" not in c and "agent = get_agent" in c:
        c = c.replace(
            "agent = get_agent",
            '''# HORUS VISUAL DIRECT INTERCEPT
    user_text = getattr(request, "message", None) or getattr(request, "content", None) or ""
    if is_visual_request(user_text):
        visual_answer = make_image_markdown(user_text)
        return {"response": visual_answer, "agent": "PIXEL", "visual": True}

    agent = get_agent''',
            1
        )

    chat.write_text(c, encoding="utf-8")

# Compile safety check
files_to_check = [
    "backend/services/visual_service.py",
    "backend/services/openrouter.py",
    "backend/agents/pixel.py",
    "backend/agents/atlas.py",
    "backend/routers/chat.py"
]

print("HORUS global quality upgrade installed.")
