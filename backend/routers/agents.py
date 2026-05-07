"""
Router de Agentes - Info y gestión de los 9 agentes HORUS
"""
from fastapi import APIRouter
from agents import AGENT_REGISTRY
from models.schemas import AgentInfo, AgentType
from typing import List

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """Lista todos los agentes disponibles con su información."""
    return [agent_class.get_info() for agent_class in AGENT_REGISTRY.values()]


@router.get("/{agent_type}", response_model=AgentInfo)
async def get_agent_info(agent_type: AgentType):
    """Obtiene información de un agente específico."""
    agent_class = AGENT_REGISTRY.get(agent_type)
    if not agent_class:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Agente {agent_type} no encontrado")
    return agent_class.get_info()
