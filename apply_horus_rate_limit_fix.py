from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

# 1) Ajustar openrouter.py
openrouter = root / "backend" / "services" / "openrouter.py"
text = openrouter.read_text(encoding="utf-8")
openrouter.with_suffix(".py.backup-rate-limit").write_text(text, encoding="utf-8")

# Modelos gratis: primero openrouter/free para evitar depender de Venice/Llama directamente
text = re.sub(
    r"FALLBACK_MODELS\s*=\s*\[[\s\S]*?\]",
    '''FALLBACK_MODELS = [
    "openrouter/free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
]''',
    text
)

# Si aparece llama-3.3 como primary directo, reemplazarlo por openrouter/free
text = text.replace(
    "meta-llama/llama-3.3-70b-instruct:free",
    "openrouter/free"
)

# Bajar tokens para velocidad y menor consumo free
text = re.sub(
    r'"max_tokens":\s*min\(max_tokens or \d+,\s*\d+\)',
    '"max_tokens": min(max_tokens or 700, 700)',
    text
)

# Asegurar temperatura natural
text = re.sub(
    r'"temperature":\s*[0-9.]+',
    '"temperature": 0.7',
    text
)

openrouter.write_text(text, encoding="utf-8")

# 2) Ajustar config.py si contiene modelos default
config = root / "backend" / "config.py"
if config.exists():
    c = config.read_text(encoding="utf-8")
    config.with_suffix(".py.backup-rate-limit").write_text(c, encoding="utf-8")

    c = c.replace("meta-llama/llama-3.3-70b-instruct:free", "openrouter/free")
    c = c.replace("qwen/qwen3-next-80b-a3b-thinking:free", "openrouter/free")
    c = c.replace("deepseek/deepseek-r1:free", "openrouter/free")

    # Si hay MODEL_PRIMARY explícito, forzarlo gratis y flexible
    c = re.sub(
        r'MODEL_PRIMARY\s*=\s*["\'][^"\']+["\']',
        'MODEL_PRIMARY = "openrouter/free"',
        c
    )

    config.write_text(c, encoding="utf-8")

# 3) Reforzar estilo en todos los agentes base si existe base.py
base = root / "backend" / "agents" / "base.py"
if base.exists():
    b = base.read_text(encoding="utf-8")
    base.with_suffix(".py.backup-style").write_text(b, encoding="utf-8")

    style_note = '''
HORUS_AGENT_STYLE = """
Responde de forma breve, natural, empática y útil.
Evita sonar robótico.
No des explicaciones largas salvo que el usuario las pida.
Si una tarea requiere otro agente, actívalo y entrega el resultado sin repetir frases genéricas.
"""
'''
    if "HORUS_AGENT_STYLE" not in b:
        b = style_note + "\n" + b

    base.write_text(b, encoding="utf-8")

print("Fix aplicado: modelos free más flexibles, menos tokens y estilo base reforzado.")
