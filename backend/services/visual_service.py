
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
