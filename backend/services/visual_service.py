
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
