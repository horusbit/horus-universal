

function looksLikeVisualPrompt(text: string) {
  if (!text) return false;

  const t = text.toLowerCase();

  const keywords = [
    "logo",
    "branding",
    "mockup",
    "render",
    "vector style",
    "high resolution",
    "corporate branding",
    "flat vector",
    "centered composition",
    "professional minimalist",
    "8k quality",
    "modern sans-serif",
    "white background"
  ];

  const matches = keywords.filter(k => t.includes(k)).length;

  return matches >= 3;
}

"use client";


import React from "react";

function buildPollinationsUrl(prompt: string) {
  const enhanced = `${prompt}, masterpiece quality, premium professional design, clean composition, sharp details, elegant layout, high-end commercial quality, no watermark, no blur`;
  return `https://image.pollinations.ai/prompt/${encodeURIComponent(enhanced)}?width=1024&height=1024&model=flux&enhance=true&nologo=true`;
}

function extractImages(text: string) {
  const images: { url: string; label: string }[] = [];

  const markdownRegex = /!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g;
  let match: RegExpExecArray | null;

  while ((match = markdownRegex.exec(text)) !== null) {
    images.push({ url: match![1], label: "Imagen generada" });
  }

  const urlRegex = /(https:\/\/image\.pollinations\.ai\/prompt\/[^\s)]+)/g;
  while ((match = urlRegex.exec(text)) !== null) {
    if (!images.find((img) => img.url === match![1])) {
      images.push({ url: match![1], label: "Imagen generada" });
    }
  }

  const horusRegex = /\[HORUS_IMAGE\]\s*prompt:\s*([\s\S]*?)\s*model:/gi;

  while ((match = horusRegex.exec(text)) !== null) {

    const prompt = match![1]?.trim();

    if (!prompt) continue;

    const url = buildPollinationsUrl(prompt);

    if (!images.find((img) => img.url === url)) {
      images.push({
        url,
        label: "Imagen HORUS"
      });
    }
  }

  return images;
}

function cleanText(text: string) {
  return text
    .replace(/!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g, "")
    .replace(/https:\/\/image\.pollinations\.ai\/prompt\/[^\s)]+/g, "")
    .replace(/\[HORUS_IMAGE\][\s\S]*?\[HORUS_IMAGE\]/gi, "")
    .trim();
}

export default function VisualMessageRenderer({ content }: { content: string }) {
  let images = extractImages(content || "");
  let text = cleanText(content || "");

  // AUTO-CONVERT RAW VISUAL PROMPTS INTO IMAGES
  if (images.length === 0 && looksLikeVisualPrompt(text)) {

    const cleanedPrompt = text
      .replace("↗ abrir", "")
      .trim();

    const url = buildPollinationsUrl(cleanedPrompt);

    images = [
      {
        url,
        label: "Imagen generada"
      }
    ];
  }

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
