from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

chat_path = root / "backend/routers/chat.py"

content = chat_path.read_text(encoding="utf-8")

# REMOVE old broken injections
content = content.replace("agent = get_agent", "__HORUS_AGENT_PLACEHOLDER__")

VISUAL_BLOCK = r'''

from urllib.parse import quote
import hashlib

VISUAL_KEYWORDS = [
    "logo",
    "imagen",
    "image",
    "render",
    "mockup",
    "branding",
    "poster",
    "flyer",
    "ui",
    "web",
    "app",
    "arquitectura",
    "casa",
    "plano",
    "visual",
    "design",
    "diseño",
]

def _is_visual_request(text: str):
    if not text:
        return False

    text = text.lower()

    return any(k in text for k in VISUAL_KEYWORDS)

def _build_visual_response(prompt: str):

    enhanced = (
        f"{prompt}, masterpiece quality, premium professional design, "
        "clean composition, sharp details, elegant layout, "
        "high-end commercial quality, no watermark, no blur"
    )

    encoded = quote(enhanced)

    seed = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)

    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024"
        f"&seed={seed}"
        f"&model=flux"
        f"&enhance=true"
        f"&nologo=true"
    )

    return {
        "response": f"""# Imagen generada

![Generated Image]({url})

Abrir imagen:
{url}
""",
        "agent": "PIXEL",
        "visual": True
    }

'''

if "VISUAL_KEYWORDS" not in content:
    content = VISUAL_BLOCK + "\n" + content

# FORCE VISUAL RETURN BEFORE LLM
TARGET = "__HORUS_AGENT_PLACEHOLDER__"

REPLACE = r'''

    user_text = getattr(request, "message", None) or getattr(request, "content", None) or ""

    # HORUS HARD VISUAL BYPASS
    if _is_visual_request(user_text):
        return _build_visual_response(user_text)

    agent = get_agent
'''

content = content.replace(TARGET, REPLACE, 1)

chat_path.write_text(content, encoding="utf-8")

print("HARD visual bypass installed.")
