-- ══════════════════════════════════════════════════════
-- HORUS Universal — Migraciones SQL (Supabase)
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- ══════════════════════════════════════════════════════

-- ── 1. Memoria de usuario ─────────────────────────────
-- Almacena hechos recordados del usuario entre sesiones.
CREATE TABLE IF NOT EXISTS user_memory (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,           -- nombre, empresa, proyecto, etc.
    value       TEXT NOT NULL,
    source      TEXT DEFAULT 'auto',     -- 'auto' | 'manual'
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, key)
);

-- RLS: cada usuario solo ve su propia memoria
ALTER TABLE user_memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_memory_select" ON user_memory
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "user_memory_insert" ON user_memory
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_memory_update" ON user_memory
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "user_memory_delete" ON user_memory
    FOR DELETE USING (auth.uid() = user_id);

-- Service role puede leer/escribir todo (para el backend)
CREATE POLICY "user_memory_service_all" ON user_memory
    USING (true) WITH CHECK (true);

-- Índice para búsquedas rápidas por user_id
CREATE INDEX IF NOT EXISTS idx_user_memory_user_id ON user_memory(user_id);

-- ── 2. Conversaciones compartidas ────────────────────
-- Guarda tokens públicos para compartir conversaciones.
CREATE TABLE IF NOT EXISTS shared_conversations (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL,       -- referencia a conversations.id
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token           TEXT NOT NULL UNIQUE DEFAULT gen_random_uuid()::text,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(conversation_id)
);

-- Sin RLS para selects públicos (necesario para /share/{token})
-- El backend usa service_role_key para leer
ALTER TABLE shared_conversations ENABLE ROW LEVEL SECURITY;

-- Solo el dueño puede crear/ver sus tokens
CREATE POLICY "shared_conv_owner" ON shared_conversations
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Service role acceso total
CREATE POLICY "shared_conv_service_all" ON shared_conversations
    USING (true) WITH CHECK (true);

-- Índice por token (búsqueda pública)
CREATE INDEX IF NOT EXISTS idx_shared_conv_token ON shared_conversations(token);

-- ── 3. Usuarios de Telegram ───────────────────────────
-- Vincula chat_id de Telegram con usuario de HORUS (opcional).
CREATE TABLE IF NOT EXISTS telegram_users (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    user_id     UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    first_name  TEXT,
    username    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_seen   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE telegram_users ENABLE ROW LEVEL SECURITY;

-- Service role acceso total
CREATE POLICY "telegram_users_service_all" ON telegram_users
    USING (true) WITH CHECK (true);

-- Índice por telegram_id
CREATE INDEX IF NOT EXISTS idx_telegram_users_tg_id ON telegram_users(telegram_id);

-- ── 4. Agentes personalizados por usuario ────────────
-- Permite a cada usuario crear sus propios agentes con
-- nombre, ícono, descripción y prompt del sistema personalizado.
CREATE TABLE IF NOT EXISTS custom_agents (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    emoji           TEXT NOT NULL DEFAULT '🤖',
    description     TEXT NOT NULL DEFAULT '',
    system_prompt   TEXT NOT NULL,
    base_model      TEXT NOT NULL DEFAULT 'google/gemini-flash-1.5',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE custom_agen