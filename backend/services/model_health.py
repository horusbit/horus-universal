"""
Health check de modelos OpenRouter — caché de modelos que fallan
para no reintentar con modelos conocidos como caídos.
"""
import time
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Tiempo que un modelo se considera "muerto" antes de reintentarlo (5 min)
COOLDOWN_SECONDS = 60

_failed_models: Dict[str, float] = {}


def mark_failed(model_id: str):
    """Marca un modelo como fallido temporalmente."""
    _failed_models[model_id] = time.time()
    logger.warning(f"[ModelHealth] {model_id} marcado como inactivo por {COOLDOWN_SECONDS}s")


def is_available(model_id: str) -> bool:
    """Retorna True si el modelo está disponible (no en cooldown)."""
    if model_id not in _failed_models:
        return True
    elapsed = time.time() - _failed_models[model_id]
    if elapsed >= COOLDOWN_SECONDS:
        del _failed_models[model_id]
        logger.info(f"[ModelHealth] {model_id} recuperado — reintentando")
        return True
    return False


def get_available_models(model_chain: list) -> list:
    """Filtra la cadena de modelos retornando solo los disponibles."""
    available = [m for m in model_chain if is_available(m)]
    skipped = [m for m in model_chain if not is_available(m)]
    if skipped:
        logger.info(f"[ModelHealth] Skipping en cooldown: {skipped}")
    return available if available else model_chain  # fallback: usar todos aunque estén en cooldown
