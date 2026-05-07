# ⚠️ Credenciales Pendientes para HORUS Universal

La clave de OpenRouter ya está configurada ✅

Faltan estas 2 credenciales para el sistema completo:

---

## 1. 🔷 Supabase (Auth + Base de datos)

Ve a: https://supabase.com/dashboard → Tu proyecto → Settings → API

Necesitas:
- `Project URL` → va en `SUPABASE_URL`
- `anon public` key → va en `SUPABASE_ANON_KEY`
- `service_role` key → va en `SUPABASE_SERVICE_ROLE_KEY`

**Archivos donde pegar:**
- `backend/.env` → busca las líneas con `SUPABASE_`
- `frontend/.env.local` → busca `NEXT_PUBLIC_SUPABASE_`

**SQL a ejecutar en Supabase (Database → SQL Editor):**
```sql
-- Habilitar Auth (ya viene por defecto en Supabase)
-- Solo necesitas activar Google/GitHub en Authentication → Providers

-- Tabla opcional para historial persistente:
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  agent TEXT NOT NULL DEFAULT 'atlas',
  title TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own conversations" ON conversations
  FOR ALL USING (auth.uid() = user_id);
```

---

## 2. 🔴 Upstash Redis (Cache de conversaciones)

Ve a: https://console.upstash.com → Tu base de datos → REST API

Necesitas:
- `UPSTASH_REDIS_REST_URL` → la URL de la base de datos
- `UPSTASH_REDIS_REST_TOKEN` → el token de acceso

**Archivo donde pegar:** `backend/.env`

> 💡 **Nota:** Sin Redis, el sistema funciona igual usando cache en memoria.
> Las conversaciones se perderán al reiniciar el servidor, pero para pruebas locales es suficiente.

---

## ✅ Pasos para arrancar HOY mismo (sin Supabase)

El sistema funciona SIN auth para pruebas locales:

1. Abre `backend/.env` y verifica que `OPENROUTER_API_KEY` esté completo ✅
2. Ejecuta `START_HORUS.bat` → opción 4 (instalar) → luego opción 3 (ambos)
3. Abre http://localhost:3000 — HORUS estará corriendo

La autenticación con Supabase es opcional para usar el sistema localmente.
