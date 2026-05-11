from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\VisualMessageRenderer.tsx")

content = path.read_text(encoding="utf-8")

# Replace match[1] with match![1]
content = content.replace("match[1]", "match![1]")

path.write_text(content, encoding="utf-8")

print("Fixed nullable regex match access.")
