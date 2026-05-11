from pathlib import Path
import re

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\routers\chat.py")

content = path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

# disable visual intercept temporarily
content = re.sub(
    r'if is_visual_request\(user_text\):.*?return\s*\{.*?\}',
    '# visual intercept temporarily disabled',
    content,
    flags=re.DOTALL
)

path.write_text(content, encoding="utf-8")

print("Disabled unstable visual intercept.")
