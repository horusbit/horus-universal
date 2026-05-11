from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

# =========================
# FIX PIXEL PROMPT
# =========================
pixel = root / "backend/agents/pixel.py"

if pixel.exists():
    p = pixel.read_text(encoding="utf-8")

    rule = '''

PIXEL_IMAGE_GENERATION_RULE = """
You CAN generate and show images.

NEVER say:
- "I cannot generate images"
- "I cannot show images directly"
- "Use Midjourney"
- "Use DALL-E externally"

Instead:
1. Generate a Pollinations image URL.
2. ALWAYS return the image in markdown format:

![Generated Image](IMAGE_URL)

3. Then give a short explanation.
4. Keep responses concise and visual-first.

Pollinations URL format:
https://image.pollinations.ai/prompt/PROMPT_HERE?width=1024&height=1024&enhance=true&nologo=true

"""
'''

    if "PIXEL_IMAGE_GENERATION_RULE" not in p:
        p = rule + "\n" + p

    pixel.write_text(p, encoding="utf-8")

# =========================
# FIX OPENROUTER GLOBAL PROMPT
# =========================
openrouter = root / "backend/services/openrouter.py"

if openrouter.exists():
    o = openrouter.read_text(encoding="utf-8")

    if "NEVER say:" not in o:
        inject = '''

GLOBAL_VISUAL_RULE = """
If the user asks for:
- logos
- architecture
- renders
- mockups
- visual concepts
- engineering visuals
- branding
- posters
- flyers
- UI
- app concepts
- images

Then:
- ALWAYS generate a Pollinations image URL.
- ALWAYS show it using markdown image syntax.

Example:

![Generated Image](https://image.pollinations.ai/prompt/modern%20logo?width=1024&height=1024&enhance=true&nologo=true)

NEVER say:
"I cannot generate images."
"""
'''

        o = inject + "\n" + o

    openrouter.write_text(o, encoding="utf-8")

print("HORUS visual prompting fixed.")
