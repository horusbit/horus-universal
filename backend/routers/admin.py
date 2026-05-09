"""
Router de Admin — HORUS Universal
Solo accesible para horuseict@gmail.com
Estadísticas, gestión de usuarios y salud del sistema.
"""
from fastapi import APIRouter, Depends, HTTPException
from auth.supabase_auth import get_optional_user
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_EMAIL = "horuseict@gmail.com"


def _require_admin(user):
    """Verifica que el usuario sea admin."""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida.")
    email = getattr(user, "email", "")
    if email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    return user


def _get_client():
    from supabase import create_client
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    )


@router.get("/stats")
async def get_stats(user=Depends(get_optional_user)):
    """Estadísticas generales del sistema."""
    _require_admin(user)
    try:
        client = _get_client()

        # Total de usuarios con plan
        plans_result = client.table("user_plans").select("plan", count="exact").execute()
        total_users = plans_result.count or 0
        plans_data = plans_result.data or []

        # Contar por plan
        plan_counts = {"free": 0, "pro": 0, "enterprise": 0, "admin": 0}
        for row in plans_data:
            plan = row.get("plan", "free")
            plan_counts[plan] = plan_counts.get(plan, 0) + 1

        # Mensajes enviados hoy
        from datetime import date
        today = date.today().isoformat()
        usage_result = client.table("daily_usage") \
            .select("message_count") \
            .eq("date", today) \
            .execute()
        messages_today = sum(r.get("message_count", 0) for r in (usage_result.data or []))

        # Total conversaciones
        conv_result = client.table("conversations").select("id", count="exact").execute()
        total_conversations = conv_result.count or 0

        # Total mensajes históricos
        msg_result = client.table("messages").select("id", count="exact").execute()
        total_messages = msg_result.count or 0

        # Top usuarios por uso hoy
        top_usage = client.table("daily_usage") \
            .select("user_id, message_count") \
            .eq("date", today) \
            .order("message_count", desc=True) \
            .limit(10) \
            .execute()

        return {
            "total_users": total_users,
            "plan_distribution": plan_counts,
            "messages_today": messages_today,
            "total_conversations": total_conversations,
            "total_messages_all_time": total_messages,
            "top_users_today": top_usage.data or [],
        }
    except Exception as e:
        logger.error(f"[Admin] stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    user=Depends(get_optional_user),
):
    """Lista todos los usuarios con su plan y uso."""
    _require_admin(user)
    try:
        client = _get_client()
        from datetime import date
        today = date.today().isoformat()

        # Obtener planes
        plans = client.table("user_plans") \
            .select("*") \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()

        if not plans.data:
            return {"users": [], "total": 0}

        # Obtener uso de hoy para estos usuarios
        user_ids = [r["user_id"] for r in plans.data]
        usage_result = client.table("daily_usage") \
            .select("user_id, message_count") \
            .eq("date", today) \
            .in_("user_id", user_ids) \
            .execute()

        usage_map = {r["user_id"]: r["message_count"] for r in (usage_result.data or [])}

        # Obtener emails desde auth (via service role)
        try:
            users_auth = client.auth.admin.list_users()
            email_map = {u.id: u.email for u in (users_auth or [])}
        except Exception:
            email_map = {}

        result = []
        for row in plans.data:
            uid = row["user_id"]
            result.append({
                "user_id": uid,
                "email": email_map.get(uid, "—"),
                "plan": row.get("plan", "free"),
                "stripe_status": row.get("stripe_status", "active"),
                "messages_today": usage_map.get(uid, 0),
                "created_at": row.get("created_at", ""),
                "period_end": row.get("current_period_end"),
            })

        total_result = client.table("user_plans").select("user_id", count="exact").execute()
        return {"users": result, "total": total_result.count or len(result)}

    except Exception as e:
        logger.error(f"[Admin] list_users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{target_user_id}/plan")
async def set_plan(
    target_user_id: str,
    body: dict,
    user=Depends(get_optional_user),
):
    """Cambia el plan de un usuario manualmente."""
    _require_admin(user)
    new_plan = body.get("plan")
    if new_plan not in ("free", "pro", "enterprise", "admin"):
        raise HTTPException(status_code=400, detail="Plan inválido.")
    try:
        client = _get_client()
        client.table("user_plans").upsert({
            "user_id": target_user_id,
            "plan": new_plan,
            "stripe_status": "active",
        }, on_conflict="user_id").execute()
        logger.info(f"[Admin] {user.email} cambió plan de {target_user_id} → {new_plan}")
        return {"success": True, "user_id": target_user_id, "new_plan": new_plan}
    except Exception as e:
        logger.error(f"[Admin] set_plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{target_user_id}/usage")
async def reset_usage(
    target_user_id: str,
    user=Depends(get_optional_user),
):
    """Reinicia el contador de uso diario de un usuario."""
    _require_admin(user)
    try:
        from datetime import date
        today = date.today().isoformat()
        client = _get_client()
        client.table("daily_usage") \
            .delete() \
            .eq("user_id", target_user_id) \
            .eq("date", today) \
            .execute()
        return {"success": True, "user_id": target_user_id, "reset_date": today}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def system_health(user=Depends(get_optional_user)):
    """Estado de todos los servicios del sistema."""
    _require_admin(user)
    health = {}

    # Supabase
    try:
        client = _get_client()
        client.table("user_plans").select("user_id").limit(1).execute()
        health["supabase"] = "ok"
    except Exception as e:
        health["supabase"] = f"error: {str(e)[:80]}"

    # Redis
    try:
        from services.redis_cache import cache
        await cache.get_conversation("health-check")
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)[:80]}"

    # OpenRouter
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            )
            health["openrouter"] = "ok" if r.status_code == 200 else f"http {r.status_code}"
    except Exception as e:
        health["openrouter"] = f"error: {str(e)[:80]}"

    # Groq STT
    health["groq_stt"] = "configured" if settings.GROQ_API_KEY else "not configured"
    # ElevenLabs TTS
    health["elevenlabs_tts"] = "configured" if settings.ELEVENLABS_API_KEY else "not configured"
    # LemonSqueezy
    health["lemonsqueezy"] = "configured" if settings.LEMONSQUEEZY_API_KEY else "not configured"

    return {"status": "operational", "services": health, "version": settings.APP_VERSION}


@router.get("/analytics")
async def get_analytics(
    days: int = 30,
    user=Depends(get_optional_user),
):
    """Analytics detallados: serie temporal, agentes, conversiones."""
    _require_admin(user)
    try:
        from datetime import date, timedelta
        client = _get_client()

        # Serie temporal: mensajes por día (últimos N días)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        usage_series = client.table("daily_usage") \
            .select("date, message_count, user_id") \
            .gte("date", start_date.isoformat()) \
            .lte("date", end_date.isoformat()) \
            .execute()

        # Agrupar por fecha
        from collections import defaultdict
        messages_by_day: dict = defaultdict(int)
        users_by_day: dict = defaultdict(set)
        for row in (usage_series.data or []):
            d = row.get("date", "")[:10]
            messages_by_day[d] += row.get("message_count", 0)
            users_by_day[d].add(row.get("user_id", ""))

        # Generar todas las fechas del rango
        timeline = []
        cursor = start_date
        while cursor <= end_date:
            ds = cursor.isoformat()
            timeline.append({
                "date": ds,
                "messages": messages_by_day.get(ds, 0),
                "active_users": len(users_by_day.get(ds, set())),
            })
            cursor += timedelta(days=1)

        # Agentes más usados (de la tabla messages)
        agents_result = client.table("messages") \
            .select("agent") \
            .not_.is_("agent", "null") \
            .gte("created_at", start_date.isoformat()) \
            .execute()

        agent_counts: dict = defaultdict(int)
        for row in (agents_result.data or []):
            a = row.get("agent", "")
            if a:
                agent_counts[a] += 1
        top_agents = sorted(
            [{"agent": k, "count": v} for k, v in agent_counts.items()],
            key=lambda x: x["count"], reverse=True
        )[:10]

        # Nuevos usuarios por semana
        users_result = client.table("user_plans") \
            .select("created_at, plan") \
            .gte("created_at", start_date.isoformat()) \
            .execute()

        new_users_by_day: dict = defaultdict(int)
        conversions_by_day: dict = defaultdict(int)
        for row in (users_result.data or []):
            d = (row.get("created_at") or "")[:10]
            if d:
                new_users_by_day[d] += 1
                if row.get("plan") == "pro":
                    conversions_by_day[d] += 1

        # Total conversiones en el período
        total_pro = client.table("user_plans") \
            .select("id", count="exact") \
            .eq("plan", "pro") \
            .execute()

        return {
            "period_days": days,
            "timeline": timeline,
            "top_agents": top_agents,
            "total_pro_users": total_pro.count or 0,
            "new_users_period": sum(new_users_by_day.values()),
            "new_conversions_period": sum(conversions_by_day.values()),
            "summary": {
                "total_messages_period": sum(messages_by_day.values()),
                "peak_day": max(timeline, key=lambda x: x["messages"])["date"] if timeline else None,
                "avg_daily_messages": round(sum(messages_by_day.values()) / max(len(timeline), 1), 1),
            }
        }
    except Exception as e:
        logger.error(f"[Admin] analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
