from pathlib import Path
import re

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

components = root / "frontend/src/components"
components.mkdir(parents=True, exist_ok=True)

renderer = components / "VisualMessageRenderer.tsx"

renderer.write_text(r'''
"use client";

import React from "react";

function buildPollinationsUrl(prompt: string) {
  const enhanced = `${prompt}, masterpiece quality, premium professional design, clean composition, sharp details, elegant layout, high-end commercial quality, no watermark, no blur`;
  return `https://image.pollinations.ai/prompt/${encodeURIComponent(enhanced)}?width=1024&height=1024&model=flux&enhance=true&nologo=true`;
}

function extractImages(text: string) {
  const images: { url: string; label: string }[] = [];

  const markdownRegex = /!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g;
  let match;

  while ((match = markdownRegex.exec(text)) !== null) {
    images.push({ url: match[1], label: "Imagen generada" });
  }

  const urlRegex = /(https:\/\/image\.pollinations\.ai\/prompt\/[^\s)]+)/g;
  while ((match = urlRegex.exec(text)) !== null) {
    if (!images.find((img) => img.url === match[1])) {
      images.push({ url: match[1], label: "Imagen generada" });
    }
  }

  const horusRegex = /\[HORUS_IMAGE\][\s\S]*?prompt:\s*([^\n\r]+)/gi;
  while ((match = horusRegex.exec(text)) !== null) {
    const prompt = match[1].trim();
    const url = buildPollinationsUrl(prompt);
    if (!images.find((img) => img.url === url)) {
      images.push({ url, label: "Imagen HORUS" });
    }
  }

  return images;
}

function cleanText(text: string) {
  return text
    .replace(/!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g, "")
    .replace(/https:\/\/image\.pollinations\.ai\/prompt\/[^\s)]+/g, "")
    .replace(/\[HORUS_IMAGE\][\s\S]*?prompt:\s*([^\n\r]+)/gi, "")
    .trim();
}

export default function VisualMessageRenderer({ content }: { content: string }) {
  const images = extractImages(content || "");
  const text = cleanText(content || "");

  return (
    <div className="space-y-4">
      {images.length > 0 && (
        <div className="grid gap-4">
          {images.map((img, index) => (
            <div key={index} className="rounded-2xl border border-white/10 bg-black/5 p-3 shadow-sm">
              <img
                src={img.url}
                alt={img.label}
                className="w-full max-w-xl rounded-xl object-contain"
                loading="lazy"
              />
              <div className="mt-2 flex gap-3 text-sm">
                <a
                  href={img.url}
                  target="_blank"
                  rel="noreferrer"
                  className="underline opacity-80 hover:opacity-100"
                >
                  Abrir imagen
                </a>
                <a
                  href={img.url}
                  download
                  className="underline opacity-80 hover:opacity-100"
                >
                  Descargar
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {text && (
        <div className="whitespace-pre-wrap leading-relaxed">
          {text}
        </div>
      )}
    </div>
  );
}
''', encoding="utf-8")

# Patch likely frontend files
targets = [
    root / "frontend/src/app/page.tsx",
    root / "frontend/src/components/ChatMessage.tsx",
    root / "frontend/src/components/MessageBubble.tsx",
    root / "frontend/src/components/ChatBubble.tsx",
]

patched = []

for path in targets:
    if not path.exists():
        continue

    txt = path.read_text(encoding="utf-8")

    if "VisualMessageRenderer" not in txt:
        txt = 'import VisualMessageRenderer from "@/components/VisualMessageRenderer";\n' + txt

    replacements = [
        (r"\{message\.content\}", r"<VisualMessageRenderer content={message.content} />"),
        (r"\{msg\.content\}", r"<VisualMessageRenderer content={msg.content} />"),
        (r"\{m\.content\}", r"<VisualMessageRenderer content={m.content} />"),
        (r"\{message\.response\}", r"<VisualMessageRenderer content={message.response} />"),
        (r"\{msg\.response\}", r"<VisualMessageRenderer content={msg.response} />"),
        (r"\{content\}", r"<VisualMessageRenderer content={content} />"),
    ]

    original = txt
    for pattern, repl in replacements:
        txt = re.sub(pattern, repl, txt)

    if txt != original:
        path.write_text(txt, encoding="utf-8")
        patched.append(str(path))

print("Visual renderer created.")
print("Patched files:")
for p in patched:
    print(p)
