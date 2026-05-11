from pathlib import Path
import re

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\routers\chat.py")

content = path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

# =========================================================
# REMOVE OLD VISUAL SYSTEMS
# =========================================================

patterns_to_remove = [
    r'VISUAL_KEYWORDS_HARD\s*=\s*\[.*?return f""".*?"""',
    r'VISUAL_KEYWORDS\s*=\s*\[.*?"visual": True\s*\}',
    r'VISUAL_FORCE_WORDS\s*=\s*\[.*?return None',
]

for pattern in patterns_to_remove:
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# =========================================================
# ENSURE IMPORTS
# =========================================================

if "from services.visual_service import is_visual_request, build_image_url" not in content:
    content = content.replace(
        "from agents import get_agent",
        "from agents import get_agent\nfrom services.visual_service import is_visual_request, build_image_url"
    )

# =========================================================
# REMOVE OLD INJECTIONS
# =========================================================

content = re.sub(
    r'# HORUS.*?agent = get_agent',
    'agent = get_agent',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'visual_result\s*=\s*_force_visual_response\(.*?return visual_result',
    '',
    content,
    flags=re.DOTALL
)

# =========================================================
# INSERT SINGLE CLEAN VISUAL SYSTEM
# =========================================================

content = content.replace(
    "agent = get_agent",
    '''
    # HORUS CLEAN STRUCTURED VISUAL SYSTEM

    user_text = (
        getattr(request, "message", None)
        or getattr(request, "content", None)
        or getattr(request, "prompt", None)
        or ""
    )

    if is_visual_request(user_text):

        image_url = build_image_url(user_text)

        return {
            "response": "Imagen generada correctamente.",
            "visual": True,
            "image_url": image_url,
            "agent": "PIXEL"
        }

    agent = get_agent
''',
    1
)

path.write_text(content, encoding="utf-8")

print("chat.py cleaned and unified.")
