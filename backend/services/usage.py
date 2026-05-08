"""
Usage & Plan Service — HORUS Universal
Controla límites de mensajes por plan y usuario.
Admin email: horuseict@gmail.com → ilimitado siempre
"""
from datetime import date
from config import settings
from models.schemas import Message
import logging

logger = logging.getLogger(__name__)

ADMIN_EMAIL = "horuseict@gmail.com"
FREE_DAILY_LIMIT = 50
PLAN_LIMITS = {
    "admin":      None,   # ilimitado
    "enterprise": None,   # ilimitado
    "pro":        None,   # ilimitado
    "free":       FREE_DAILY_LIMIT,
}


def _get_client():
    from supabase import create_client
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    )


async def get_user_plan(user_id: str) -> dict:
    """Devuelve el plan del usuario. Si no existe, lo crea como 'free'."""
    try:
        client = _get_client()
        result = client.table("user_plans").select("*").eq("user_id", user_id).single().execute()
        if result.data:
            return result.data
    except Exception:
        pass

    # Crear plan free por defecto
    try:
        client = _get_client()
        client.table("user_plans").insert({
            "user_id": user_id,
            "plan": "free",
        }).execute()
    except Exception as e:
        logger.warning(f"[Usage] No se pudo crear plan: {e}")

    return {"user_id": user_id, "plan": "free", "stripe_status": "active"}


async def get_daily_usage(user_id: str) -> int:
    """Devuelve los mensajes usados hoy."""
    try:
        client = _get_client()
        today = date.today().isoformat()
        result = client.table("daily_usage") \
            .select("message_count") \
            .eq("user_id", user_id) \
            .eq("date", today) \
            .execute()
        if result.data:
            return result.data[0]["message_count"]
    except Exception as e:
        logger.warning(f"[Usage] get_daily_usage error: {e}")
    return 0


async def increment_usage(user_id: str) -> int:
    """Incrementa el contador de mensajes de hoy. Devuelve el nuevo total."""
    try:
        client = _get_client()
        # Upsert: crea o incrementa
        client.rpc("increment_daily_usage", {"p_user_id": user_id}).execute()
        return await get_daily_usage(user_id)
    except Exception as e:
        logger.warning(f"[Usage] increment_usage error: {e}")
        return 0


async def check_usage_limit(user, user_email: str = "") -> dict:
    """
    Verifica si el usuario puede enviar un mensaje.
    Devuelve: {"allowed": bool, "plan": str, "used": int, "limit": int | None}
    """
    # Sin usuario autenticado → permitir (modo anónimo/dev)
    if not user:
        return {"allowed": True, "plan": "anonymous", "used": 0, "limit": None}

    # Admin email → siempre ilimitado
    if user_email == ADMIN_EMAIL or getattr(user, "email", "") == ADMIN_EMAIL:
        return {"allowed": True, "plan": "admin", "used": 0, "limit": None}

    plan_data = await get_user_plan(user.id)
    plan = plan_data.get("plan", "free")
    limit = PLAN_LIMITS.get(plan)

    # Plan ilimitado
    if limit is None:
        return {"allowed": True, "plan": plan, "used": 0, "limit": None}

    # Verificar uso diario
    used = await get_daily_usage(user.id)
    allowed = used < limit

    return {
        "allowed": allowed,
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
    }


async def set_user_plan(user_id: str, plan: str, stripe_customer_id: str = None,
                        stripe_subscription_id: str = None, stripe_status: str = "active",
                        period_end=None) -> bool:
    """Actualiza el plan de un usuario (usado por webhook de Stripe)."""
    try:
        client = _get_client()
        data = {"plan": plan, "stripe_status": stripe_status}
        if stripe_customer_id:
            data["stripe_customer_id"] = stripe_customer_id
        if stripe_subscription_id:
            data["stripe_subscription_id"] = stripe_subscription_id
        if period_end:
            data["current_period_end"] = period_end

        client.table("user_plans").upsert({
            "user_id": user_id,
            **data,
        }, on_conflict="user_id").execute()
        return True
    except Exception as e:
        logger.error(f"[Usage] set_user_plan error: {e}")
        return False
