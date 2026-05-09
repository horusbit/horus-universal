"""
Router de Agentes Personalizados — HORUS Universal
Permite a cada usuario crear, editar y eliminar sus propios agentes con
nombre, ícono, descripción y prompt del sistema personalizado.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from services.supabase_db import (
    list_custom_agents, create_custom_agent, get_custom_agent,
    update_custom_agent, delete_custom_agent,
)
from auth.supabase_auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/custom", tags=["custom-agents"])

ALLOWED_MODELS = [
    "google/gemini-flash-1.5",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o-mini",
]


class CustomAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    emoji: str = Field(default="🤖", max_length=8)
    description: str = Field(default="", max_length=200)
    system_prompt: str = Field(..., min_length=10, max_length=4000)
    base_model: str = Field(default="google/gemini-flash-1.5")


class CustomAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=40)
    emoji: Optional[str] = Field(None, max_length=8)
    description: Optional[str] = Field(None, max_length=200)
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=4000)
    base_model: Optional[str] = None


class CustomAgentOut(BaseModel):
    id: str
    name: str
    emoji: str
    description: str
    system_prompt: str
    base_model: str
    created_at: Optional[str] = None


@router.get("/", response_model=List[CustomAgentOut])
async def list_agents(user=Depends(get_current_user)):
    """Lista todos los agentes personalizados del usuario autenticado."""
    agents = await list_custom_agents(user["id"])
    return agents


@router.post("/", response_model=CustomAgentOut, status_code=201)
async def create_agent(body: CustomAgentCreate, user=Depends(get_current_user)):
    """Crea un nuevo agente personalizado."""
    # Validar modelo
    if body.base_model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail=f"Modelo no permitido. Usa uno de: {', '.join(ALLOWED_MODELS)}")
    # Límite: máximo 10 agentes personalizados por usuario
    existing = await list_custom_agents(user["id"])
    if len(existing) >= 10:
        raise HTTPException(status_code=400, detail="Límite de 10 agentes personalizados alcanzado.")
    agent = await create_custom_agent(
        user_id=user["id"],
        name=body.name,
        emoji=body.emoji or "🤖",
        description=body.description or "",
        system_prompt=body.system_prompt,
        base_model=body.base_model,
    )
    if not agent:
        raise HTTPException(status_code=500, detail="Error creando agente.")
    return agent


@router.get("/{agent_id}", response_model=CustomAgentOut)
async def get_agent(agent_id: str, user=Depends(get_current_user)):
    """Obtiene un agente personalizado por ID."""
    agent = await get_custom_agent(agent_id, user["id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    return agent


@router.put("/{agent_id}", response_model=CustomAgentOut)
async def update_agent(agent_id: str, body: CustomAgentUpdate, user=Depends(get_current_user)):
    """Actualiza un agente personalizado."""
    existing = await get_custom_agent(agent_id, user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if body.base_model and body.base_model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail=f"Modelo no permitido.")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        return existing
    await update_custom_agent(agent_id, user["id"], **fields)
    return await get_custom_agent(agent_id, user["id"])


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, user=Depends(get_current_user)):
    """Elimina un agente personalizado."""
    existing = await get_custom_agent(agent_id, user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    await delete_custom_agent(agent_id, user["id"])
    return None


@router.get("/models/available")
async def get_available_models(user=Depends(get_current_user)):
    """Lista los modelos disponibles para agentes personalizados."""
    return {"models": ALLOWED_MODELS}
