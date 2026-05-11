import subprocess
import re

file_path = "backend/routers/chat.py"

log = subprocess.check_output(
    ["git", "log", "--reverse", "--format=%H%x09%s", "--", file_path],
    text=True,
    encoding="utf-8",
    errors="ignore"
)

visual_words = re.compile(r"(visual|image|imagen|pollinations|render)", re.I)

first_bad = None

for line in log.splitlines():
    if "\t" not in line:
        continue
    commit, msg = line.split("\t", 1)
    if visual_words.search(msg):
        first_bad = commit
        break

if not first_bad:
    raise SystemExit("No encontre commits visuales tocando chat.py. Pegame git log --oneline -- backend/routers/chat.py")

stable_ref = first_bad + "^"

subprocess.check_call(["git", "checkout", stable_ref, "--", file_path])

print(f"chat.py restaurado desde version estable antes de: {first_bad}")
