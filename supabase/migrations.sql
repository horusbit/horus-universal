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

DROP POLICY IF EXISTS "user_memory_select" ON user_memory;
CREATE POLICY "user_memory_select" ON user_memory
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_memory_insert" ON user_memory;
CREATE POLICY "user_memory_insert" ON user_memory
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_memory_update" ON user_memory;
CREATE POLICY "user_memory_update" ON user_memory
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_memory_delete" ON user_memory;
CREATE POLICY "user_memory_delete" ON user_memory
    FOR DELETE USING (auth.uid() = user_id);

-- Service role puede leer/escribir todo (para el backend)
DROP POLICY IF EXISTS "user_memory_service_all" ON user_memory;
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
DROP POLICY IF EXISTS "shared_conv_owner" ON shared_conversations;
CREATE POLICY "shared_conv_owner" ON shared_conversations
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Service role acceso total
DROP POLICY IF EXISTS "shared_conv_service_all" ON shared_conversations;
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
DROP POLICY IF EXISTS "telegram_users_service_all" ON telegram_users;
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

ALTER TABLE custom_agents ENABLE ROW LEVEL SECURITY;

-- Cada usuario solo ve/gestiona sus propios agentes
DROP POLICY IF EXISTS "custom_agents_owner" ON custom_agents;
CREATE POLICY "custom_agents_owner" ON custom_agents
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Service role acceso total
DROP POLICY IF EXISTS "custom_agents_service_all" ON custom_agents;
CREATE POLICY "custom_agents_service_all" ON custom_agents
    USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_custom_agents_user_id ON custom_agents(user_id);

-- ── 5. Función para updated_at automático ────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS custom_agents_updated_at ON custom_agents;
CREATE TRIGGER custom_agents_updated_at
    BEFORE UPDATE ON custom_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS user_memory_updated_at ON user_memory;
CREATE TRIGGER user_memory_updated_at
    BEFORE UPDATE ON user_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ══════════════════════════════════════════════════════
-- TABLAS BASE — conversations, messages, user_plans, daily_usage
-- IMPORTANTE: ejecutar esto si las tablas no existen aún
-- ══════════════════════════════════════════════════════

-- ── Conversaciones ────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL DEFAULT 'Nueva conversación',
    agent       TEXT NOT NULL DEFAULT 'atlas',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "conv_owner" ON conversations;
CREATE POLICY "conv_owner" ON conversations
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "conv_service_all" ON conversations;
CREATE POLICY "conv_service_all" ON conversations
    USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- ── Mensajes ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    agent           TEXT,
    model_used      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "messages_owner" ON messages;
CREATE POLICY "messages_owner" ON messages
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = conversation_id AND c.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = conversation_id AND c.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "messages_service_all" ON messages;
CREATE POLICY "messages_service_all" ON messages
    USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- ── Planes de usuario ─────────────────────────────────
CREATE TABLE IF NOT EXISTS user_plans (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    plan        TEXT NOT NULL DEFAULT 'free',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_plans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_plans_owner" ON user_plans;
CREATE POLICY "user_plans_owner" ON user_plans
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "user_plans_service_all" ON user_plans;
CREATE POLICY "user_plans_service_all" ON user_plans
    USING (true) WITH CHECK (true);

-- ── Uso diario ────────────────────────────────────────
-- ── Uso diario ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_usage (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date        DATE NOT NULL DEFAULT CURRENT_DATE,
    count       INT NOT NULL DEFAULT 0,
    UNIQUE(user_id, date)
);

ALTER TABLE daily_usage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "daily_usage_owner" ON daily_usage;
CREATE POLICY "daily_usage_owner" ON daily_usage
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "daily_usage_service_all" ON daily_usage;
CREATE POLICY "daily_usage_service_all" ON daily_usage
    USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, date);

-- ── Trigger updated_at para conversations ────────────
DROP TRIGGER IF EXISTS conversations_updated_at ON conversations;
CREATE TRIGGER conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── Teams / Workspace ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    owner_id UUID NOT NULL,
    plan TEXT DEFAULT 'team',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    email TEXT DEFAULT '',
    role TEXT DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "team_members_select" ON team_members;
CREATE POLICY "team_members_select" ON team_members
    FOR SELECT USING (user_id = auth.uid() OR
        team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "team_members_insert" ON team_members;
CREATE POLICY "team_members_insert" ON team_members
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "teams_select" ON teams;
CREATE POLICY "teams_select" ON teams
    FOR SELECT USING (
        id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "teams_insert" ON teams;
CREATE POLICY "teams_insert" ON teams
    FOR ALL USING (true) WITH CHECK (true);
