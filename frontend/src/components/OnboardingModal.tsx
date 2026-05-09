"use client";

import { useState, useEffect } from "react";

const STEPS = [
  {
    icon: "👁",
    title: "Bienvenido a HORUS Universal",
    desc: "Tu orquestador personal de IA con 16 agentes especializados. Cada agente domina su área — código, marketing, legal, datos, ventas y más.",
    tip: null,
  },
  {
    icon: "🌐",
    title: "ATLAS lo enruta todo automáticamente",
    desc: "Escribe cualquier pregunta y ATLAS detecta qué agente es el más adecuado. O elige el agente directamente desde el selector arriba.",
    tip: "Tip: escribe \"crea una API en Python\" y ATLAS te enruta a CIPHER automáticamente.",
  },
  {
    icon: "🧠",
    title: "HORUS te recuerda",
    desc: "El sistema aprende sobre ti entre sesiones. Si mencionas tu nombre, empresa o proyecto, lo recordará en futuros chats.",
    tip: "Tip: escribe \"mi empresa se llama Bullion RD\" y HORUS lo recordará siempre.",
  },
  {
    icon: "🎨",
    title: "PIXEL genera imágenes reales",
    desc: "Pídele a PIXEL que cree un logo, banner o ilustración y aparecerá directamente en el chat. Gratis, sin límites.",
    tip: "Tip: selecciona PIXEL y escribe \"crea un logo minimalista para una startup de fintech\".",
  },
  {
    icon: "🔗",
    title: "Comparte y exporta",
    desc: "Puedes compartir cualquier conversación con un link público, exportarla como Markdown o PDF, y escuchar las respuestas en voz.",
    tip: "Los botones aparecen al pasar el cursor sobre cualquier respuesta.",
  },
];

interface OnboardingModalProps {
  onComplete: () => void;
}

export default function OnboardingModal({ onComplete }: OnboardingModalProps) {
  const [step, setStep] = useState(0);
  const [animating, setAnimating] = useState(false);

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  const goNext = () => {
    if (animating) return;
    if (isLast) { onComplete(); return; }
    setAnimating(true);
    setTimeout(() => { setStep(s => s + 1); setAnimating(false); }, 200);
  };

  const goBack = () => {
    if (animating || step === 0) return;
    setAnimating(true);
    setTimeout(() => { setStep(s => s - 1); setAnimating(false); }, 200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#12121a] border border-[#1e1e2e] rounded-2xl overflow-hidden shadow-2xl">

        {/* Progress bar */}
        <div className="h-1 bg-[#1e1e2e]">
          <div
            className="h-full bg-indigo-500 transition-all duration-500"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className={`p-8 transition-opacity duration-200 ${animating ? "opacity-0" : "opacity-100"}`}>
          <div className="text-center mb-6">
            <div className="text-5xl mb-4">{current.icon}</div>
            <h2 className="text-xl font-bold text-[#e2e8f0] mb-3">{current.title}</h2>
            <p className="text-[#94a3b8] text-sm leading-relaxed">{current.desc}</p>
          </div>

          {current.tip && (
            <div className="bg-indigo-950/40 border border-indigo-500/20 rounded-xl px-4 py-3 mb-6">
              <p className="text-xs text-indigo-300 leading-relaxed">{current.tip}</p>
            </div>
          )}

          {/* Step dots */}
          <div className="flex justify-center gap-1.5 mb-6">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`rounded-full transition-all ${
                  i === step ? "w-4 h-1.5 bg-indigo-500" : "w-1.5 h-1.5 bg-[#1e1e2e]"
                }`}
              />
            ))}
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            {step > 0 && (
              <button
                onClick={goBack}
                className="flex-1 py-2.5 border border-[#1e1e2e] hover:border-indigo-500/50
                  text-[#64748b] hover:text-white text-sm rounded-lg transition-all"
              >
                ← Atrás
              </button>
            )}
            <button
              onClick={goNext}
              className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm
                font-medium rounded-lg transition-all"
            >
              {isLast ? "¡Empezar! →" : "Siguiente →"}
            </button>
          </div>

          {/* Skip */}
          {!isLast && (
            <button
              onClick={onComplete}
              className="w-full mt-3 text-xs text-[#475569] hover:text-[#64748b] transition-colors"
            >
              Saltar introducción
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
