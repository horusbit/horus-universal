"""
Router de Billing — HORUS Universal
Integración con Lemon Squeezy para suscripciones Pro
"""
import hmac
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from config import settings
from services.usage import get_user_plan, set_user_plan, check_usage_limit
from auth.supabase_auth import get_optional_user
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

LS_API_URL = "https://api.lemonsqueezy.com/v1"


def _ls_headers():
    return {
        "Authorization": f"Bearer {settings.LEMONSQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


# ── Crear checkout ───────────────────────────────────────────────────────────

@router.post("/checkout")
async def create_checkout(user=Depends(get_optional_user)):
    """Crea un checkout de Lemon Squeezy para el plan Pro."""
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión para suscribirte.")

    if not settings.LEMONSQUEEZY_API_KEY:
        raise HTTPException(status_code=503, detail="Billing no configurado.")

    user_email = getattr(user, "email", "")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LS_API_URL}/checkouts",
                headers=_ls_headers(),
                json={
                    "data": {
                        "type": "checkouts",
                        "attributes": {
                            "checkout_data": {
                                "email": user_email,
                                "custom": {"user_id": user.id},
                            },
                            "product_options": {
                                "redirect_url": "https://horus-universal.vercel.app/?upgraded=true",
                                "receipt_link_url": "https://horus-universal.vercel.app/",
                            },
                        },
                        "relationships": {
                            "store": {
                                "data": {"type": "stores", "id": str(settings.LEMONSQUEEZY_STORE_ID)}
                            },
                            "variant": {
                                "data": {"type": "variants", "id": str(settings.LEMONSQUEEZY_VARIANT_ID)}
                            },
                        },
                    }
                },
            )

        if response.status_code not in (200, 201):
            logger.error(f"[LemonSqueezy] checkout error: {response.text}")
            raise HTTPException(status_code=502, detail="Error creando checkout.")

        data = response.json()
        checkout_url = data["data"]["attributes"]["url"]
        return {"checkout_url": checkout_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LemonSqueezy] checkout exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Plan actual del usuario ───────────────────────────────────────────────────

@router.get("/plan")
async def get_plan(user=Depends(get_optional_user)):
    """Devuelve el plan y uso actual del usuario."""
    if not user:
        return {"plan": "anonymous", "used": 0, "limit": 50, "allowed": True}

    user_email = getattr(user, "email", "")
    usage = await check_usage_limit(user, user_email)
    plan_data = await get_user_plan(user.id)

    return {
        "plan": usage["plan"],
        "used": usage.get("used", 0),
        "limit": usage.get("limit"),
        "remaining": usage.get("remaining"),
        "allowed": usage["allowed"],
        "stripe_status": plan_data.get("stripe_status", "active"),
        "period_end": plan_data.get("current_period_end"),
    }


# ── Webhook de Lemon Squeezy ──────────────────────────────────────────────────

@router.post("/webhook")
async def lemonsqueezy_webhook(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature"),
):
    """Recibe eventos de Lemon Squeezy y actualiza planes."""
    body = await request.body()

    # Verificar firma si hay webhook secret configurado
    if settings.LEMONSQUEEZY_WEBHOOK_SECRET and x_signature:
        expected = hmac.new(
            settings.LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, x_signature):
            raise HTTPException(status_code=401, detail="Firma inválida")

    try:
        payload = json.loads(body)
        event_name = payload.get("meta", {}).get("event_name", "")
        custom_data = payload.get("meta", {}).get("custom_data", {})
        user_id = custom_data.get("user_id")

        logger.info(f"[LemonSqueezy] Webhook: {event_name}, user_id={user_id}")

        if not user_id:
            return {"received": True}

        attrs = payload.get("data", {}).get("attributes", {})
        customer_id = str(attrs.get("customer_id", ""))
        subscription_id = str(payload.get("data", {}).get("id", ""))
        status = attrs.get("status", "active")
        ends_at = attrs.get("ends_at")

        if event_name in ("subscription_created", "subscription_updated", "subscription_resumed"):
            await set_user_plan(
                user_id=user_id,
                plan="pro",
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                stripe_status=status,
                period_end=ends_at,
            )
            logger.info(f"[LemonSqueezy] ✅ Usuario {user_id} → Pro")

        elif event_name in ("subscription_cancelled", "subscription_expired", "subscription_paused"):
            await set_user_plan(
                user_id=user_id,
                plan="free",
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                stripe_status=status,
            )
            logger.info(f"[LemonSqueezy] ⬇️ Usuario {user_id} → Free")

        return {"received": True}

    except Exception as e:
        logger.error(f"[LemonSqueezy] Webhook error: {e}")
        return {"received": True}
