from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\VisualMessageRenderer.tsx")

content = path.read_text(encoding="utf-8")

content = content.replace(
    r'/\[HORUS_IMAGE\]\s*prompt:\s*(.*?)\s*model:/gis',
    r'/\[HORUS_IMAGE\]\s*prompt:\s*([\s\S]*?)\s*model:/gi'
)

# Also replace cleanup regex if it uses s flag
content = content.replace(
    r'/\[HORUS_IMAGE\][\s\S]*?\[HORUS_IMAGE\]/gis',
    r'/\[HORUS_IMAGE\][\s\S]*?\[HORUS_IMAGE\]/gi'
)

path.write_text(content, encoding="utf-8")

print("Fixed regex flags compatibility.")
