from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\app\page.tsx")

content = path.read_text(encoding="utf-8")

# Remove misplaced directive/import combo
content = content.replace(
    'import VisualMessageRenderer from "@/components/VisualMessageRenderer";\n"use client";',
    '"use client";\n\nimport VisualMessageRenderer from "@/components/VisualMessageRenderer";'
)

# Ensure use client is FIRST line
if '"use client";' in content:
    lines = content.splitlines()

    # Remove all existing use client lines
    lines = [l for l in lines if l.strip() != '"use client";']

    # Reinsert at top
    lines.insert(0, '"use client";')
    content = "\n".join(lines)

path.write_text(content, encoding="utf-8")

print("Fixed Next.js use client order.")
