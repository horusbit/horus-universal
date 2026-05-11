from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

chat_path = root / "backend/routers/chat.py"

content = chat_path.read_text(encoding="utf-8")

# Ensure imports
if "from urllib.parse import quote" not in content:
    content = "from urllib.parse import quote\n" + content

if "import hashlib" not in content:
    content = "import hashlib\n" + content

if "VISUAL_FORCE_WORDS" not in content:
    helper = r'''

VISUAL_FORCE_WORDS = [
    "logo", "imagen", "image", "render", "mockup",
    "branding", "arquitectura", "casa", "plano",
    "poster", "flyer", "ui", "web", "app",
    "diseño", "design", "visual"
]

def _force_visual_response(user_text: str):
    if not user_text:
        return None

    low = user_text.lower()

    if not any(w in low for w in VISUAL_FORCE_WORDS):
        return None

    enhanced = (
        f"{user_text}, masterpiece quality, premium professional design, "
        "sharp details, clean composition, high-end commercial quality, "
        "balanced symmetry, elegant, no watermark, no blur"
    )

    encoded = quote(enhanced)

    seed = int(hashlib.sha256(user_text.encode()).hexdigest()[:8], 16)

    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024&seed={seed}"
        f"&model=flux&enhance=true&nologo=true"
    )

    return {
        "response": f"""# Propuesta visual

![Generated Image]({url})

Abrir imagen:
{url}

Concepto generado:
{enhanced}
""",
        "agent": "PIXEL",
        "visual": True
    }

'''
    content = helper + "\n" + content

# Inject BEFORE agent loading
if "_force_visual_response(user_text)" not in content:

    pattern = r'agent\s*=\s*get_agent'

    replacement = r'''
    # FORCE VISUAL IMAGE RESPONSE
    user_text = getattr(request, "message", None) or getattr(request, "content", None) or ""

    visual_result = _force_visual_response(user_text)

    if visual_result:
        return visual_result

    agent = get_agent
'''

    content = re.sub(pattern, replacement, content, count=1)

chat_path.write_text(content, encoding="utf-8")

print("FORCED visual markdown response installed.")
