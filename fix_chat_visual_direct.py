from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

visual_service = root / "backend/services/visual_service.py"
visual_service.parent.mkdir(parents=True, exist_ok=True)

visual_service.write_text('''
from urllib.parse import quote

VISUAL_WORDS = [
    "logo", "imagen", "image", "render", "mockup", "branding",
    "diseño", "diseno", "arquitectura", "plano", "casa",
    "poster", "flyer", "banner", "ui", "app", "web", "visual"
]

def is_visual_request(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(w in t for w in VISUAL_WORDS)

def make_image_markdown(prompt: str) -> str:
    enhanced = (
        prompt.strip()
        + ", high quality, professional, premium design, sharp details, "
        + "clean composition, no watermark"
    )
    url = "https://image.pollinations.ai/prompt/" + quote(enhanced) + "?width=1024&height=1024&enhance=true&nologo=true"
    return f"""Te prepare una propuesta visual inicial:

![Imagen generada]({url})

Abrir imagen:
{url}

Prompt usado:
{enhanced}
"""
''', encoding="utf-8")

chat_path = root / "backend/routers/chat.py"
chat = chat_path.read_text(encoding="utf-8")

if "from services.visual_service import is_visual_request, make_image_markdown" not in chat:
    chat = chat.replace(
        "from agents import get_agent",
        "from agents import get_agent\nfrom services.visual_service import is_visual_request, make_image_markdown"
    )

# Inserta interceptacion visual dentro del archivo, justo antes de usar get_agent si encuentra el texto.
if "HORUS VISUAL DIRECT INTERCEPT" not in chat:
    chat = chat.replace(
        "agent = get_agent",
        '''
    # HORUS VISUAL DIRECT INTERCEPT
    user_text = getattr(request, "message", None) or getattr(request, "content", None) or ""
    if is_visual_request(user_text):
        visual_answer = make_image_markdown(user_text)
        return {"response": visual_answer, "agent": "PIXEL", "visual": True}

    agent = get_agent''',
        1
    )

chat_path.write_text(chat, encoding="utf-8")

print("Visual direct intercept installed in chat router.")
