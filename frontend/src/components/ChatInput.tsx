"use client";

import { useState, useRef, useEffect, useCallback, RefObject } from "react";
import { transcribeAudio } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function extractFile(file: File): Promise<{ text?: string; context?: string; filename: string; type: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const r = await fetch(`${API_URL}/api/v1/upload/`, { method: "POST", body: formData });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Error procesando archivo");
  }
  return r.json();
}

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  placeholder?: string;
  inputRef?: React.RefObject<HTMLTextAreaElement>;
  onVoiceSend?: (text: string) => void;
}

type VoiceState = "idle" | "recording" | "transcribing" | "error";

export default function ChatInput({ onSend, isLoading, placeholder, inputRef, onVoiceSend }: ChatInputProps) {
  const [text, setText] = useState("");
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [voiceError, setVoiceError] = useState<string>("");
  const [recordingTime, setRecordingTime] = useState(0);
  const [fileLoading, setFileLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<{ name: string; type: string } | null>(null);
  const [showDrivePanel, setShowDrivePanel] = useState(false);

  const internalRef = useRef<HTMLTextAreaElement>(null);
  const textareaRef = (inputRef as RefObject<HTMLTextAreaElement>) || internalRef;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [text]);

  // Limpiar timer al desmontar
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stopStream();
    };
  }, []);

  const stopStream = () => {
    if (mediaRecorderRef.current?.stream) {
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileLoading(true);
    try {
      const result = await extractFile(file);
      const prefix = result.context || `[Archivo: ${result.filename}]\n`;
      setText(prev => prefix + (prev || "Analiza este archivo y respóndeme sobre su contenido."));
      setAttachedFile({ name: result.filename, type: result.type });
      textareaRef.current?.focus();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error procesando archivo");
    } finally {
      setFileLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setText("");
    setAttachedFile(null);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startRecording = useCallback(async () => {
    setVoiceError("");
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Determinar el mejor formato soportado
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/mp4")
        ? "audio/mp4"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stopStream();
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

        if (audioBlob.size < 1000) {
          setVoiceState("idle");
          return;
        }

        setVoiceState("transcribing");
        try {
          const transcript = await transcribeAudio(audioBlob);
          if (transcript) {
            const fullText = text ? `${text} ${transcript}` : transcript;
            if (onVoiceSend) {
              setVoiceState("idle");
              onVoiceSend(fullText);
              setText("");
            } else {
              setText(fullText);
              textareaRef.current?.focus();
              setVoiceState("idle");
            }
          } else {
            setVoiceState("idle");
          }
        } catch (err: any) {
          // Fallback: Web Speech API (se usa cuando no hay GROQ_API_KEY o hay error)
          const useBrowserFallback = err?.message === "use_browser_stt" || err?.message?.includes("503");
          const fallbackResult = await fallbackWebSpeech();
          if (fallbackResult) {
            setText(prev => prev ? `${prev} ${fallbackResult}` : fallbackResult);
            setVoiceState("idle");
          } else {
            setVoiceError(useBrowserFallback
              ? "STT del servidor no disponible. Habla directo al micrófono."
              : "Error al transcribir. Intenta de nuevo.");
            setVoiceState("error");
            setTimeout(() => setVoiceState("idle"), 3000);
          }
        }
      };

      recorder.start(250); // recopilar chunks cada 250ms
      setVoiceState("recording");
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(t => {
          if (t >= 59) {
            stopRecording();
            return 0;
          }
          return t + 1;
        });
      }, 1000);

    } catch (err: any) {
      if (err.name === "NotAllowedError") {
        setVoiceError("Permiso de micrófono denegado");
      } else {
        setVoiceError("No se pudo acceder al micrófono");
      }
      setVoiceState("error");
      setTimeout(() => setVoiceState("idle"), 3000);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const toggleVoice = () => {
    if (voiceState === "recording") {
      stopRecording();
    } else if (voiceState === "idle" || voiceState === "error") {
      startRecording();
    }
  };

  // Fallback a Web Speech API si no hay Groq
  const fallbackWebSpeech = (): Promise<string> => {
    return new Promise((resolve) => {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) { resolve(""); return; }
      const recognition = new SpeechRecognition();
      recognition.lang = "es-ES";
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onresult = (e: any) => resolve(e.results[0][0].transcript);
      recognition.onerror = () => resolve("");
      recognition.onend = () => resolve("");
      try { recognition.start(); } catch { resolve(""); }
    });
  };

  const micLabel = {
    idle: "🎤",
    recording: "⏹",
    transcribing: "⏳",
    error: "🎤",
  }[voiceState];

  const micClass = {
    idle: "text-[#64748b] hover:text-[#e2e8f0] hover:bg-[#1e1e2e]",
    recording: "bg-red-500/20 text-red-400",
    transcribing: "bg-indigo-500/20 text-indigo-400",
    error: "bg-yellow-500/20 text-yellow-400",
  }[voiceState];

  return (
    <div className="space-y-1">
      {/* Archivo adjunto */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.jpg,.jpeg,.png,.webp"
        onChange={handleFileSelect}
        className="hidden"
      />
      {attachedFile && (
        <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
          <span>📎</span>
          <span className="truncate">{attachedFile.name}</span>
          <button onClick={() => { setAttachedFile(null); setText(""); }} className="ml-auto hover:text-red-400">✕</button>
        </div>
      )}
      {/* Error / estado de voz */}
      {(voiceState === "recording" || voiceState === "transcribing" || voiceError) && (
        <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg
          ${voiceState === "recording"
            ? "bg-red-500/10 text-red-400"
            : voiceState === "transcribing"
            ? "bg-indigo-500/10 text-indigo-400"
            : "bg-yellow-500/10 text-yellow-400"
          }`}>
          {voiceState === "recording" && (
            <>
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span>Grabando... {recordingTime}s (máx 60s)</span>
              <button onClick={stopRecording} className="ml-auto underline">Detener</button>
            </>
          )}
          {voiceState === "transcribing" && (
            <>
              <span className="w-3 h-3 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
              <span>Transcribiendo con Groq Whisper...</span>
            </>
          )}
          {voiceState === "error" && voiceError && <span>{voiceError}</span>}
        </div>
      )}

      {/* Input principal */}
      <div className="flex items-end gap-2 bg-[#12121a] border border-[#1e1e2e] rounded-2xl px-3 py-2
        focus-within:border-indigo-500/50 transition-colors">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder || "Escribe un mensaje..."}
          disabled={isLoading}
          rows={1}
          className="flex-1 bg-transparent text-[#e2e8f0] text-sm resize-none outline-none
            placeholder:text-[#475569] disabled:opacity-50 py-1 max-h-40"
        />
        <div className="flex items-center gap-1 flex-shrink-0 pb-1">
          {/* Botón adjuntar archivo */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={fileLoading || isLoading}
            title="Adjuntar PDF, DOCX, TXT o imagen"
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all
              text-[#64748b] hover:text-[#e2e8f0] hover:bg-[#1e1e2e] disabled:opacity-50"
          >
            {fileLoading ? (
              <span className="w-3 h-3 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
            ) : "📎"}
          </button>
          {/* Botón Google Drive */}
          <button
            onClick={() => setShowDrivePanel(p => !p)}
            disabled={isLoading}
            title="Adjuntar desde Google Drive"
            className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all
              disabled:opacity-50
              ${showDrivePanel ? "bg-green-600/20 text-green-400" : "text-[#64748b] hover:text-[#e2e8f0] hover:bg-[#1e1e2e]"}
            `}
          >
            <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
              <path d="M6.6 6L2 14.4h4.8L11.4 6H6.6zm.6 9.6L4.8 19.2h14.4l-2.4-3.6H7.2zm10.2-9.6L12 15.6l2.4 3.6L22 6h-4.6z"/>
            </svg>
          </button>
          {/* Botón de micrófono */}
          <button
            onClick={toggleVoice}
            disabled={voiceState === "transcribing" || isLoading}
            title={
              voiceState === "recording"
                ? "Detener grabación"
                : voiceState === "transcribing"
                ? "Transcribiendo..."
                : "Grabar mensaje de voz"
            }
            className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all
              disabled:opacity-50 disabled:cursor-not-allowed
              ${micClass}
              ${voiceState === "recording" ? "animate-pulse" : ""}`}
          >
            {micLabel}
          </button>

          {/* Botón de enviar */}
          <button
            onClick={handleSend}
            disabled={!text.trim() || isLoading}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-colors
              bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : "↑"}
          </button>
        </div>
      </div>
    </div>
  );
}
