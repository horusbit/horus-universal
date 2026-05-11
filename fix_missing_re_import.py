from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\routers\chat.py")

content = path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

if "import re" not in content:

    imports = [
        "from fastapi",
        "from pydantic",
        "import uuid",
        "from uuid"
    ]

    inserted = False

    for imp in imports:
        idx = content.find(imp)

        if idx != -1:
            content = content[:idx] + "import re\n" + content[idx:]
            inserted = True
            break

    if not inserted:
        content = "import re\n" + content

path.write_text(content, encoding="utf-8")

print("Added missing import re")
