from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\routers\chat.py")

content = path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

content = content.replace(
    "from services.visual_service import is_visual_request, make_image_markdown",
    "from services.visual_service import is_visual_request, build_image_url"
)

path.write_text(content, encoding="utf-8")

print("Removed old make_image_markdown import.")
