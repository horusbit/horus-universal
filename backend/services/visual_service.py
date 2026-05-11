
from urllib.parse import quote
import hashlib

VISUAL_KEYWORDS = [
    "logo", "image", "imagen", "branding", "render",
    "mockup", "poster", "flyer", "ui", "web",
    "arquitectura", "casa", "plano", "visual",
    "design", "diseño", "diseno"
]

def is_visual_request(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    return any(k in text for k in VISUAL_KEYWORDS)

def build_image_url(prompt: str) -> str:

    enhanced = (
        f"{prompt}, masterpiece quality, premium professional design, "
        "sharp details, clean composition, elegant layout, "
        "high-end commercial quality, no watermark, no blur"
    )

    encoded = quote(enhanced)

    seed = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)

    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024"
        f"&height=1024"
        f"&seed={seed}"
        f"&model=flux"
        f"&enhance=true"
        f"&nologo=true"
    )
