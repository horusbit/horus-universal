from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\services\openrouter.py")

content = path.read_text(encoding="utf-8-sig")

# Remove all invisible BOM characters anywhere in the file
content = content.replace("\ufeff", "")

path.write_text(content, encoding="utf-8")

print("All U+FEFF characters removed from openrouter.py")
