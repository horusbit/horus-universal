# 👁 HORUS Universal

Orquestador personal de IA multi-modelo. 9 agentes especializados, arquitectura de costo cero.

## Stack
- **Backend**: FastAPI → Render (free)
- **Frontend**: Next.js + PWA → Vercel (free)
- **Auth + DB**: Supabase (free)
- **Cache**: Upstash Redis (free)
- **IA**: OpenRouter (Llama 3.3, Gemini Flash, DeepSeek gratis + Claude Haiku para tareas críticas)

## Agentes
| Agente | Especialidad |
|--------|-------------|
| 🌐 ATLAS | Orquestador maestro |
| ⚡ CIPHER | Código y desarrollo |
| ✨ NOVA | Marketing y copywriting |
| ⚖️ LEXIS | Documentos legales |
| 🔮 ORACLE | Estrategia de negocios |
| 🌍 HERMES | Traducción |
| 🎙️ ECHO | Voz y audio |
| 🔬 DARWIN | Investigación |
| 🎨 PIXEL | Generación de imágenes |

---

## 🚀 Setup Rápido (Día 1)

### 1. Configurar Variables de Entorno

**Backend** — copia `backend/.env.example` como `backend/.env`:
```
SUPABASE_URL=tu-url
SUPABASE_ANON_KEY=tu-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-key
OPENROUTER_API_KEY=tu-openrouter-key
UPSTASH_REDIS_REST_URL=tu-redis-url
UPSTASH_REDIS_REST_TOKEN=tu-redis-token
```

**Frontend** — copia `frontend/.env.example` como `frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=tu-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Correr Backend (local)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

### 3. Correr Frontend (local)
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## 📦 Deploy a Producción

### Backend → Render
1. Push a GitHub
2. New Web Service en render.com → conecta repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Agregar variables de entorno del `.env.example`

### Frontend → Vercel
1. `vercel --prod` desde la carpeta `frontend/`
2. O conecta el repo en vercel.com
3. Agregar variables de entorno del `.env.example`

### Supabase — SQL a ejecutar
```sql
-- Tabla de conversaciones (opcional, el cache usa Redis)
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  agent TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own conversations" ON conversations
  FOR ALL USING (auth.uid() = user_id);
```

---

## 📅 Sprint Restante

| Día | Objetivo |
|-----|----------|
| ✅ Día 1 | Backend FastAPI + Frontend Next.js |
| Día 2 | LiteLLM proxy + Sistema de agentes avanzado |
| Día 3 | Integración de voz + Redis cache |
| Día 4 | Generación de imágenes + memoria |
| Día 5 | Testing + Deploy completo |
