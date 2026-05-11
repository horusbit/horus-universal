from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

page = root / "frontend/src/app/page.tsx"
bubble = root / "frontend/src/components/MessageBubble.tsx"

# Fix page.tsx: content must remain string
p = page.read_text(encoding="utf-8")

p = re.sub(
    r'content=<VisualMessageRenderer content=\{msg\.content\} />',
    r'content={msg.content}',
    p
)

# Remove unused import from page if present
p = p.replace('import VisualMessageRenderer from "@/components/VisualMessageRenderer";\n', '')

# Ensure use client stays first if present
if '"use client";' in p:
    lines = [line for line in p.splitlines() if line.strip() != '"use client";']
    lines.insert(0, '"use client";')
    p = "\n".join(lines) + "\n"

page.write_text(p, encoding="utf-8")

# Fix MessageBubble: render visuals inside component
b = bubble.read_text(encoding="utf-8")

if 'import VisualMessageRenderer from "@/components/VisualMessageRenderer";' not in b:
    b = b.replace(
        '"use client";\n',
        '"use client";\n\nimport VisualMessageRenderer from "@/components/VisualMessageRenderer";\n',
        1
    )

# Replace common markdown rendering of content with VisualMessageRenderer
# Keep it broad but safe
b = re.sub(
    r'<ReactMarkdown([^>]*)>\{content\}</ReactMarkdown>',
    r'<VisualMessageRenderer content={content} />',
    b
)

b = re.sub(
    r'\{content\}',
    r'<VisualMessageRenderer content={content} />',
    b,
    count=1
)

# Fix accidental nested replacements
b = b.replace(
    '<VisualMessageRenderer content=<VisualMessageRenderer content={content} /> />',
    '<VisualMessageRenderer content={content} />'
)

# Ensure use client first
if '"use client";' in b:
    lines = [line for line in b.splitlines() if line.strip() != '"use client";']
    lines.insert(0, '"use client";')
    b = "\n".join(lines) + "\n"

bubble.write_text(b, encoding="utf-8")

print("Fixed content prop and MessageBubble visual rendering.")
