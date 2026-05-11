from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

# Clean BOM
for p in (root / "backend").rglob("*.py"):
    txt = p.read_text(encoding="utf-8-sig").replace("\ufeff", "")
    p.write_text(txt, encoding="utf-8")

# Ensure OpenRouter payload is conservative
openrouter = root / "backend/services/openrouter.py"
txt = openrouter.read_text(encoding="utf-8")

txt = re.sub(
    r'FALLBACK_MODELS\s*=\s*\[[\s\S]*?\]',
    '''FALLBACK_MODELS = [
    "openrouter/free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
]''',
    txt
)

txt = txt.replace("meta-llama/llama-3.3-70b-instruct:free", "openrouter/free")
txt = txt.replace("qwen/qwen3-next-80b-a3b-thinking:free", "openrouter/free")

# Keep tokens low
txt = re.sub(r'"max_tokens":\s*min\(max_tokens or \d+,\s*\d+\)', '"max_tokens": min(max_tokens or 700, 700)', txt)

openrouter.write_text(txt, encoding="utf-8")

print("OpenRouter stability patch applied.")
