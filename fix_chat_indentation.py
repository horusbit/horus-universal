from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\routers\chat.py")

content = path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

# Find first real import
marker = "from fastapi"

idx = content.find(marker)

if idx != -1:
    content = content[idx:]

# Prepend ONLY clean visual imports
header = '''
from services.visual_service import is_visual_request, build_image_url

'''

content = header + content

path.write_text(content, encoding="utf-8")

print("Cleaned broken indentation/header from chat.py")
