-- ============================================================
-- HORUS Universal — Setup Supabase SQL
-- Ejecuta este SQL en: Supabase > SQL Editor > New query
-- ============================================================

-- ── Tabla de conversaciones ──────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
  id          TEXT PRIMARY KEY,
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  title       TEXT NOT NULL DEFAULT 'Nueva conversación',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice para buscar por usuario
CREATE INDEX IF NOT EXISTS idx_conversations_user_id
  ON conversations(user_id, updated_at DESC);

-- ── Tabla de mensajes ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content         TEXT NOT NULL,
  agent           TEXT,
  model_used      TEXT,
  tokens_used     INTEGER,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice para cargar mensajes de una conversación
CREATE INDEX IF NOT EXISTS idx_messages_conversation
  ON messages(conversation_id, created_at ASC);

-- ── Trigger: actualizar updated_at en conversations ──────────
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE conversations
  SET updated_at = NOW()
  WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation
AFTER INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION update_conversation_timestamp();

-- ── Row Level Security (RLS) ──────────────────────────────────
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Usuarios autenticados ven solo sus conversaciones
CREATE POLICY "Users see own conversations" ON conversations
  FOR ALL USING (auth.uid() = user_id);

-- Usuarios ven mensajes de sus conversaciones
CREATE POLICY "Users see own messages" ON messages
  FOR ALL USING (
    conversation_id IN (
      SELECT id FROM conversations WHERE user_id = auth.uid()
    )
  );

-- Acceso de servicio (backend con service role key, sin RLS)
-- El backend usa SUPABASE_SERVICE_ROLE_KEY que bypass RLS automáticamente.

-- ── Vista: últimas conversaciones con resumen ────────────────
CREATE OR REPLACE VIEW conversation_summaries AS
SELECT
  c.id,
  c.user_id,
  c.title,
  c.created_at,
  c.updated_at,
  COUNT(m.id) AS message_count,
  (
    SELECT content
    FROM messages
    WHERE conversation_id = c.id
    ORDER BY created_at DESC
    LIMIT 1
  ) AS last_message
FROM conversations c
LEFT JOIN messages m ON m.conversation_id = c.id
GROUP BY c.id;

-- ── Tabla de uso de voz (Fase 2) ────────────────────────────
CREATE TABLE IF NOT EXISTS voice_usage (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  operation       TEXT NOT NULL CHECK (operation IN ('stt', 'tts')),
  provider        TEXT NOT NULL,
  duration_seconds FLOAT,
  characters_count INTEGER,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INSTRUCCIONES POST-SETUP:
-- 1. Copia y pega este SQL en Supabase > SQL Editor > New query
-- 2. Haz clic en "Run"
-- 3. Verifica que las tablas aparecen en Table Editor
-- 4. Asegúrate de que SUPABASE_SERVICE_ROLE_KEY está en Render env vars
-- ============================================================
