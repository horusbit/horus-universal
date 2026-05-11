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
