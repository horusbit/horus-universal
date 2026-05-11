from pathlib import Path
import re

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\services\openrouter.py")

content = path.read_text(encoding="utf-8")

HELPER = '''

from urllib.parse import quote


VISUAL_KEYWORDS = [
    "logo",
    "image",
    "imagen",
    "visual",
    "branding",
    "architecture",
    "arquitectura",
    "render",
    "mockup",
    "ui",
    "poster",
    "flyer",
    "design",
    "diseno",
    "diseño",
    "house",
    "casa",
]


def _is_visual_request(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    return any(k in text for k in VISUAL_KEYWORDS)


def _build_pollinations_markdown(prompt: str) -> str:
    encoded = quote(prompt)

    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&enhance=true&nologo=true"

    return f"""
![Generated Image]({url})

Visual generated for:
{prompt}
"""
'''

if "_build_pollinations_markdown" not in content:
    content = HELPER + "\n" + content

# Force image markdown injection before returning responses
PATTERN = r"return response_text"

REPLACEMENT = '''
if _is_visual_request(user_message):
        return _build_pollinations_markdown(user_message)

    return response_text
'''

content = re.sub(PATTERN, REPLACEMENT, content)

path.write_text(content, encoding="utf-8")

print("Automatic visual markdown injection installed.")
