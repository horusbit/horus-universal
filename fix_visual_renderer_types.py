from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\VisualMessageRenderer.tsx")

content = path.read_text(encoding="utf-8")

content = content.replace(
    "let match;",
    "let match: RegExpExecArray | null;"
)

path.write_text(content, encoding="utf-8")

print("Fixed VisualMessageRenderer TypeScript match type.")
