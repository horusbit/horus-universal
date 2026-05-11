from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\VisualMessageRenderer.tsx")

content = path.read_text(encoding="utf-8")

# Remove all existing use client lines
lines = [line for line in content.splitlines() if line.strip() != '"use client";']

# Add use client at absolute top
lines.insert(0, '"use client";')

new_content = "\n".join(lines) + "\n"

path.write_text(new_content, encoding="utf-8")

print("Moved use client to top of VisualMessageRenderer.")
