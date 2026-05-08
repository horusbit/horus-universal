"use client";

import { useRouter } from "next/navigation";

const AGENTS = [
  { icon: "🌐", name: "ATLAS",    desc: "Orquestador maestro — enruta al agente correcto automáticamente" },
  { icon: "⚡", name: "CIPHER",   desc: "Código, APIs, debugging, arquitectura y DevOps" },
  { icon: "✨", name: "NOVA",     desc: "Marketing, copywriting viral y contenido para redes" },
  { icon: "⚖️", name: "LEXIS",    desc: "Contratos, documentos legales y compliance" },
  { icon: "🔮", name: "ORACLE",   desc: "Estrategia de negocios, finanzas y modelos de negocio" },
  { icon: "🌍", name: "HERMES",   desc: "Traducción en 50+ idiomas con adaptación cultural" },
  { icon: "🎙️", name: "ECHO",     desc: "Scripts de audio/video, podcasts y guiones" },
  { icon: "🔬", name: "DARWIN",   desc: "Investigación, análisis de datos y fact-checking" },
  { icon: "🎨", name: "PIXEL",    desc: "Prompts para Midjourney, DALL-E y diseño visual" },
  { icon: "📡", name: "NEXUS",    desc: "Estrategia de redes sociales e Instagram/TikTok" },
  { icon: "📊", name: "FORGE",    desc: "Excel, SQL, Python/Pandas y Business Intelligence" },
  { icon: "🎓", name: "SAGE",     desc: "Tutorías, educación y explicaciones paso a paso" },
  { icon: "💼", name: "VECTOR",   desc: "Ventas, CRM, scripts y manejo de objeciones" },
  { icon: "⏱️", name: "CHRONOS",  desc: "Productividad, planificación y gestión del tiempo" },
  { icon: "🏛️", name: "POLITEIA", desc: "Política, campañas electorales y estrategia de gobierno" },
  { icon: "🏫", name: "EDUCRAFT", desc: "Plataformas educativas virtuales tipo edX/Coursera" },
];

const FEATURES = [
  { icon: "🚀", title: "16 Agentes Especializados", desc: "Cada agente domina su área: código, marketing, legal, datos, ventas, educación, política y más." },
  { icon: "🔄", title: "Auto-routing Inteligente", desc: "ATLAS detecta automáticamente qué agente es el más adecuado para cada solicitud." },
  { icon: "🧠", title: "Modelos de IA de Vanguardia", desc: "Gemini, Llama 70B, DeepSeek y más — con fallback automático para máxima disponibilidad." },
  { icon: "🎙️", title: "Voz y Audio", desc: "Graba mensajes de voz con Groq Whisper y escucha respuestas con ElevenLabs TTS." },
  { icon: "📎", title: "Sube Archivos", desc: "Analiza PDFs, Word, imágenes y más. El contexto del archivo se incluye en la conversación." },
  { icon: "💾", title: "Historial Persistente", desc: "Todas tus conversaciones se guardan en Supabase y están disponibles desde cualquier dispositivo." },
  { icon: "📱", title: "App Instalable (PWA)", desc: "Instala HORUS en tu iPhone o Android como una app nativa, sin pasar por el App Store." },
  { icon: "💰", title: "Arquitectura de Costo Cero", desc: "Modelos gratuitos de OpenRouter. Plan Free: 50 mensajes/día. Plan Pro: ilimitado." },
];

const PRICING = [
  {
    name: "Free",
    price: "$0",
    period: "siempre",
    color: "border-[#1e1e2e]",
    badge: "",
    features: ["50 mensajes por día", "16 agentes especializados", "Historial de conversaciones", "Voz (STT + TTS)", "Subida de archivos", "App móvil (PWA)"],
    cta: "Empezar gratis",
    ctaStyle: "border border-indigo-500/50 text-indigo-400 hover:bg-indigo-500/10",
    href: "/register",
  },
  {
    name: "Pro",
    price: "$10",
    period: "/ mes",
    color: "border-indigo-500/50",
    badge: "⚡ Más popular",
    features: ["Mensajes ilimitados", "16 agentes especializados", "Historial de conversaciones", "Voz (STT + TTS)", "Subida de archivos", "App móvil (PWA)", "Prioridad en respuestas", "Soporte prioritario"],
    cta: "Empezar Pro",
    ctaStyle: "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white",
    href: "/register",
  },
];

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="h-screen overflow-y-auto bg-[#0a0a0f] text-[#e2e8f0]" style={{ overflowY: "auto" }}>

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#1e1e2e]/80 bg-[#0a0a0f]/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center text-sm">👁</div>
            <span className="font-bold text-sm">HORUS Universal</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => router.push("/login")} className="text-xs text-[#64748b] hover:text-white px-3 py-1.5 transition-colors">
              Iniciar sesión
            </button>
            <button
              onClick={() => router.push("/register")}
              className="text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
            >
              Empezar gratis
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-28 pb-20 px-4 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 text-xs text-indigo-400 mb-6">
            <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-pulse" />
            16 agentes especializados — arquitectura de costo cero
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
            Tu equipo de IA{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
              especializado
            </span>
          </h1>
          <p className="text-[#94a3b8] text-lg sm:text-xl max-w-2xl mx-auto mb-8 leading-relaxed">
            HORUS Universal reúne 16 agentes de IA expertos en código, marketing, legal, ventas, datos, educación, política y más — en una sola plataforma.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => router.push("/register")}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500
                text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-indigo-500/20"
            >
              Empezar gratis — sin tarjeta
            </button>
            <button
              onClick={() => router.push("/login")}
              className="px-6 py-3 border border-[#1e1e2e] hover:border-indigo-500/50 text-[#94a3b8]
                hover:text-white rounded-xl text-sm transition-all"
            >
              Ya tengo cuenta →
            </button>
          </div>
          <p className="text-xs text-[#475569] mt-4">50 mensajes gratis al día · Sin tarjeta de crédito</p>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 border-t border-[#1e1e2e]">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">Todo lo que necesitas en uno</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 hover:border-indigo-500/30 transition-colors">
                <div className="text-2xl mb-3">{f.icon}</div>
                <h3 className="text-sm font-semibold mb-2">{f.title}</h3>
                <p className="text-xs text-[#64748b] leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Agents Grid */}
      <section className="py-16 px-4 border-t border-[#1e1e2e]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold mb-3">16 Agentes Especializados</h2>
            <p className="text-[#64748b] text-sm max-w-xl mx-auto">
              Cada agente tiene un sistema de prompts profundo, conocimiento especializado y acceso a los mejores modelos de IA para su área.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {AGENTS.map((agent) => (
              <div
                key={agent.name}
                className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 hover:border-indigo-500/30 transition-all hover:-translate-y-0.5"
              >
                <div className="text-2xl mb-2">{agent.icon}</div>
                <div className="text-sm font-bold mb-1">{agent.name}</div>
                <div className="text-xs text-[#64748b] leading-relaxed">{agent.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-16 px-4 border-t border-[#1e1e2e]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold mb-3">Precios simples y transparentes</h2>
            <p className="text-[#64748b] text-sm">Empieza gratis. Actualiza cuando lo necesites.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-2xl mx-auto">
            {PRICING.map((plan) => (
              <div key={plan.name} className={`bg-[#12121a] border ${plan.color} rounded-2xl p-6 relative`}>
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-xs px-3 py-1 rounded-full whitespace-nowrap">
                    {plan.badge}
                  </div>
                )}
                <div className="mb-4">
                  <h3 className="font-bold text-lg">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-[#64748b] text-sm">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-2 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-xs text-[#94a3b8]">
                      <span className="text-green-400 flex-shrink-0">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => router.push(plan.href)}
                  className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all ${plan.ctaStyle}`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-20 px-4 border-t border-[#1e1e2e]">
        <div className="max-w-2xl mx-auto text-center">
          <div className="text-5xl mb-6">👁</div>
          <h2 className="text-2xl sm:text-3xl font-bold mb-4">
            El asistente de IA más completo que vas a usar
          </h2>
          <p className="text-[#64748b] text-sm mb-8 leading-relaxed">
            16 agentes expertos, voz, archivos, historial permanente, app móvil. Todo gratis para empezar.
          </p>
          <button
            onClick={() => router.push("/register")}
            className="px-8 py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500
              text-white rounded-xl font-medium transition-all shadow-lg shadow-indigo-500/20 text-sm"
          >
            Crear cuenta gratuita
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-indigo-600 rounded flex items-center justify-center text-xs">👁</div>
            <span className="text-sm font-medium">HORUS Universal</span>
          </div>
          <p className="text-xs text-[#475569]">Powered by OpenRouter · Supabase · Vercel · 16 agentes de IA</p>
          <div className="flex gap-4">
            <button onClick={() => router.push("/login")} className="text-xs text-[#64748b] hover:text-white transition-colors">Login</button>
            <button onClick={() => router.push("/register")} className="text-xs text-[#64748b] hover:text-white transition-colors">Registro</button>
          </div>
        </div>
      </footer>
    </div>
  );
}
