from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src")

fixed = []

for path in root.rglob("*.tsx"):
    content = path.read_text(encoding="utf-8")

    if '"use client";' in content:
        lines = content.splitlines()

        # Remove all existing use client directives
        lines = [line for line in lines if line.strip() != '"use client";']

        # Put it as absolute first line
        lines.insert(0, '"use client";')

        new_content = "\n".join(lines) + "\n"

        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            fixed.append(str(path))

print("Fixed use client in:")
for f in fixed:
    print(f)
