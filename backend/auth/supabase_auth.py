from fastapi import HTTPException, Depends, Header
from typing import Optional
from models.schemas import UserProfile
import logging

logger = logging.getLogger(__name__)

# Supabase es opcional - si no está instalado, auth funciona en modo desarrollo
try:
    from supabase import create_client, Client
    from config import settings
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase no disponible - auth en modo desarrollo (sin restricciones)")

_supabase = None

def get_supabase():
    global _supabase
    if not SUPABASE_AVAILABLE:
        return None
    if _supabase is None:
        from config import settings
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _supabase


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> UserProfile:
    # Modo desarrollo: si supabase no está, retorna usuario demo
    if not SUPABASE_AVAILABLE:
        return UserProfile(id="dev-user", email="dev@horus.local", full_name="Dev User")

    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato invalido. Use: Bearer <token>")

    token = parts[1]
    try:
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token invalido")
        user = user_response.user
        return UserProfile(
            id=str(user.id),
            email=user.email or "",
            full_name=user.user_metadata.get("full_name") if user.user_metadata else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error auth: {e}")
        raise HTTPException(status_code=401, detail="Error verificando token")


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[UserProfile]:
    if not SUPABASE_AVAILABLE:
        return UserProfile(id="dev-user", email="dev@horus.local", full_name="Dev User")
    if not authorization:
        return None
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
