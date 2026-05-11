from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")
chat_path = root / "backend/routers/chat.py"

content = chat_path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

# 1. Add imports
if "from urllib.parse import quote" not in content:
    content = "from urllib.parse import quote\n" + content

if "import hashlib" not in content:
    content = "import hashlib\n" + content

# 2. Add hard visual helper
helper = r'''
VISUAL_KEYWORDS_HARD = [
    "logo", "imagen", "image", "render", "mockup", "branding",
    "poster", "flyer", "ui", "web", "app", "arquitectura",
    "casa", "plano", "visual", "design", "diseño", "diseno",
    "foto", "ilustracion", "ilustración", "arte"
]

def _horus_is_visual(text: str) -> bool:
    if not text:
        return False
    text = text.lower()
    return any(k in text for k in VISUAL_KEYWORDS_HARD)

def _horus_visual_markdown(prompt: str) -> str:
    enhanced = (
        f"{prompt}, masterpiece quality, premium professional design, "
        "clean composition, sharp details, elegant layout, high-end commercial quality, "
        "balanced symmetry, no watermark, no blur"
    )

    encoded = quote(enhanced)
    seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)

    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024&seed={seed}&model=flux&enhance=true&nologo=true"
    )

    return f"""# Imagen generada

![Imagen generada]({url})

Abrir imagen:
{url}
"""
'''

if "VISUAL_KEYWORDS_HARD" not in content:
    content = helper + "\n" + content

# 3. Inject before every get_agent usage
content = content.replace(
    "agent = get_agent(",
    '''user_text = getattr(request, "message", None) or getattr(request, "content", None) or getattr(request, "prompt", None) or ""
    if _horus_is_visual(user_text):
        return {"response": _horus_visual_markdown(user_text), "agent": "PIXEL", "visual": True}

    agent = get_agent('''
)

# 4. Inject before common streaming generators
content = content.replace(
    "async def event_generator",
    '''async def event_generator'''
)

# 5. For streaming responses, force direct SSE before model if request is visual
stream_patch = r'''
    user_text = getattr(request, "message", None) or getattr(request, "content", None) or getattr(request, "prompt", None) or ""
    if _horus_is_visual(user_text):
        answer = _horus_visual_markdown(user_text)
        async def visual_event_generator():
            yield f"data: {answer}\\n\\n"
        return StreamingResponse(visual_event_generator(), media_type="text/event-stream")
'''

if "visual_event_generator" not in content:
    content = content.replace(
        "try:",
        stream_patch + "\n    try:",
        1
    )

chat_path.write_text(content, encoding="utf-8")

print("Hard visual bypass injected into chat and stream paths.")
