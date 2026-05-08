"""
Router de Conversaciones Compartidas — HORUS Universal
Acceso público (sin auth) para ver conversaciones compartidas por token.
"""
from fastapi import APIRouter, HTTPException
from services.supabase_db import get_shared_conversation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["share"])


@router.get("/{token}")
async def get_shared(token: str):
    """
    Devuelve la conversación compartida públicamente.
    No requiere autenticación.
    """
    if not token or len(token) < 10:
        raise HTTPException(status_code=400, detail="Token inválido.")

    data = await get_shared_conversation(token)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada o el enlace expiró."
        )
    return data
