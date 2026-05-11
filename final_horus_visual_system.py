from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

# =========================================================
# BACKEND VISUAL SERVICE
# =========================================================

visual_service = root / "backend/services/visual_service.py"

visual_service.parent.mkdir(parents=True, exist_ok=True)

visual_service.write_text(r'''
from urllib.parse import quote
import hashlib

VISUAL_KEYWORDS = [
    "logo", "image", "imagen", "branding", "render",
    "mockup", "poster", "flyer", "ui", "web",
    "arquitectura", "casa", "plano", "visual",
    "design", "diseño", "diseno"
]

def is_visual_request(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    return any(k in text for k in VISUAL_KEYWORDS)

def build_image_url(prompt: str) -> str:

    enhanced = (
        f"{prompt}, masterpiece quality, premium professional design, "
        "sharp details, clean composition, elegant layout, "
        "high-end commercial quality, no watermark, no blur"
    )

    encoded = quote(enhanced)

    seed = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)

    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024"
        f"&height=1024"
        f"&seed={seed}"
        f"&model=flux"
        f"&enhance=true"
        f"&nologo=true"
    )
''', encoding="utf-8")

# =========================================================
# PATCH CHAT ROUTER
# =========================================================

chat_path = root / "backend/routers/chat.py"

chat = chat_path.read_text(encoding="utf-8-sig").replace("\ufeff", "")

# imports
if "from services.visual_service import is_visual_request, build_image_url" not in chat:
    chat = chat.replace(
        "from agents import get_agent",
        "from agents import get_agent\nfrom services.visual_service import is_visual_request, build_image_url"
    )

# inject BEFORE get_agent
pattern = r'agent\s*=\s*get_agent'

replacement = r'''
    user_text = getattr(request, "message", None) or getattr(request, "content", None) or getattr(request, "prompt", None) or ""

    # HORUS STRUCTURED VISUAL RESPONSE
    if is_visual_request(user_text):

        image_url = build_image_url(user_text)

        return {
            "response": "Imagen generada correctamente.",
            "visual": True,
            "image_url": image_url,
            "agent": "PIXEL"
        }

    agent = get_agent
'''

chat = re.sub(pattern, replacement, chat, count=1)

chat_path.write_text(chat, encoding="utf-8")

# =========================================================
# FRONTEND VISUAL RENDERER
# =========================================================

renderer = root / "frontend/src/components/VisualMessageRenderer.tsx"

renderer.parent.mkdir(parents=True, exist_ok=True)

renderer.write_text(r'''
"use client";

import React from "react";

type Props = {
  content?: string;
  imageUrl?: string;
  visual?: boolean;
};

export default function VisualMessageRenderer({
  content,
  imageUrl,
  visual
}: Props) {

  return (
    <div className="space-y-4">

      {visual && imageUrl && (
        <div className="rounded-2xl border border-white/10 bg-black/5 p-3 shadow-sm">
          <img
            src={imageUrl}
            alt="Generated"
            className="w-full max-w-2xl rounded-xl object-contain"
          />

          <div className="mt-2">
            <a
              href={imageUrl}
              target="_blank"
              rel="noreferrer"
              className="underline text-sm opacity-80 hover:opacity-100"
            >
              Abrir imagen
            </a>
          </div>
        </div>
      )}

      {content && (
        <div className="whitespace-pre-wrap leading-relaxed">
          {content}
        </div>
      )}
    </div>
  );
}
''', encoding="utf-8")

# =========================================================
# PATCH MESSAGEBUBBLE
# =========================================================

bubble = root / "frontend/src/components/MessageBubble.tsx"

if bubble.exists():

    b = bubble.read_text(encoding="utf-8")

    if 'import VisualMessageRenderer from "@/components/VisualMessageRenderer";' not in b:

        if '"use client";' in b:
            b = b.replace(
                '"use client";',
                '"use client";\n\nimport VisualMessageRenderer from "@/components/VisualMessageRenderer";'
            )
        else:
            b = 'import VisualMessageRenderer from "@/components/VisualMessageRenderer";\n' + b

    # Replace first content render
    b = re.sub(
        r'\{content\}',
        r'<VisualMessageRenderer content={content} imageUrl={(message as any)?.image_url} visual={(message as any)?.visual} />',
        b,
        count=1
    )

    bubble.write_text(b, encoding="utf-8")

# =========================================================
# CLEAN USE CLIENT
# =========================================================

for tsx in (root / "frontend/src").rglob("*.tsx"):

    c = tsx.read_text(encoding="utf-8")

    if '"use client";' in c:

        lines = [line for line in c.splitlines() if line.strip() != '"use client";']

        lines.insert(0, '"use client";')

        tsx.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("HORUS structured visual system installed.")
