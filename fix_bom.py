from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\services\openrouter.py")

# Leer removiendo BOM
content = path.read_text(encoding="utf-8-sig")

# Guardar limpio UTF-8 normal
path.write_text(content, encoding="utf-8")

print("BOM removed from openrouter.py")
