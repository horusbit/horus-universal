from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")
openrouter = root / "backend" / "services" / "openrouter.py"

text = openrouter.read_text(encoding="utf-8")
backup = openrouter.with_suffix(".py.backup-speed-style")
backup.write_text(text, encoding="utf-8")

# 1) Limitar fallback models a 3 modelos rápidos/free
text = re.sub(
    r"FALLBACK_MODELS\s*=\s*\[[\s\S]*?\]",
    '''FALLBACK_MODELS = [
    "openrouter/free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]''',
    text
)

# 2) Agregar normalizador y capa de estilo si no existen
helper = r'''
HORUS_STYLE_SYSTEM_PROMPT = """
You are HORUS / ATLAS, a premium AI assistant.

Style:
- Be warm, natural, concise and useful.
- Respond like ChatGPT, Claude or Gemini: clear, empathetic and human.
- Keep answers short by default.
- Expand only when the user asks for detail.
- Avoid robotic, corporate or overly formal language.
- Avoid excessive bullet points and long introductions.
- Prioritize direct action, clarity and practical help.
- Match the user's language.
"""

def _normalize_messages(messages):
    normalized = []

    for msg in messages:
        if isinstance(msg, dict):
            normalized.append(msg)
        elif hasattr(msg, "model_dump"):
            normalized.append(msg.model_dump())
        elif hasattr(msg, "dict"):
            normalized.append(msg.dict())
        else:
            normalized.append({
                "role": getattr(msg, "role", "user"),
                "content": getattr(msg, "content", str(msg))
            })

    # Add HORUS conversational style layer only if no system message exists
    has_system = any(m.get("role") == "system" for m in normalized if isinstance(m, dict))
    if not has_system:
        normalized.insert(0, {
            "role": "system",
            "content": HORUS_STYLE_SYSTEM_PROMPT
        })

    return normalized
'''

if "HORUS_STYLE_SYSTEM_PROMPT" not in text:
    text = text.replace("def _build_payload", helper + "\n\ndef _build_payload")

# 3) Reemplazar _build_payload completo para usar un solo modelo y mensajes normalizados
text = re.sub(
    r"def _build_payload\([\s\S]*?\n\s*return payload",
    '''def _build_payload(models_list, messages, temperature, max_tokens, stream=False):
    selected_model = models_list[0] if isinstance(models_list, list) and len(models_list) > 0 else "openrouter/free"

    payload = {
        "model": selected_model,
        "messages": _normalize_messages(messages),
        "temperature": 0.7,
        "max_tokens": min(max_tokens or 900, 900),
        "stream": stream,
    }

    return payload''',
    text
)

# 4) Protección extra: cualquier lista de modelos queda limitada a 3
text = re.sub(
    r"models_list\s*=\s*_build_models_list\(primary\)(?!\[:3\])",
    "models_list = _build_models_list(primary)[:3]",
    text
)

openrouter.write_text(text, encoding="utf-8")
print("openrouter.py actualizado correctamente.")
