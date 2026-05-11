from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\agents\pixel.py")

content = path.read_text(encoding="utf-8")

RULE = '''

POLLINATIONS_IMAGE_RULE = """
For ANY visual request:
- logo
- image
- architecture
- render
- mockup
- branding
- poster
- flyer
- UI
- visual concept

You MUST ALWAYS return a markdown image.

Format EXACTLY like this:

![Generated Image](https://image.pollinations.ai/prompt/PROCESSED_PROMPT_HERE?width=1024&height=1024&enhance=true&nologo=true)

After the image, give a SHORT explanation.

NEVER:
- say you cannot generate images
- only provide prompts
- only provide descriptions
- only provide HTML
- ask users to use Midjourney externally

The image URL MUST always be included directly.
"""
'''

if "POLLINATIONS_IMAGE_RULE" not in content:
    content = RULE + "\n" + content

path.write_text(content, encoding="utf-8")

print("PIXEL forced to return markdown image URLs.")
