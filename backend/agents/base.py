
HORUS_AGENT_STYLE = """
Responde de forma breve, natural, empática y útil.
Evita sonar robótico.
No des explicaciones largas salvo que el usuario las pida.
Si una tarea requiere otro agente, actívalo y entrega el resultado sin repetir frases genéricas.
"""

"""
Clase base para todos los agentes HORUS
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from models.schemas import Message, AgentType, ModelTier, AgentInfo
from services.openrouter import chat_completion, chat_stream


class BaseAgent(ABC):
    agent_type: AgentType
    name: str
    description: str
    icon: str
    capabilities: List[str]
    preferred_tier: ModelTier = ModelTier.FREE_BALANCED
    system_prompt: str = ""

    @classmethod
    def get_info(cls) -> AgentInfo:
        return AgentInfo(
            id=cls.agent_type,
            name=cls.name,
            description=cls.description,
            icon=cls.icon,
            capabilities=cls.capabilities,
            preferred_model=cls.preferred_tier.value,
        )

    @classmethod
    def build_messages(
        cls,
        user_message: str,
        history: List[Message],
        extra_system_context: str = "",
    ) -> List[Message]:
        """Construye la lista de mensajes con system prompt del agente.
        extra_system_context se añade al final del system prompt (ej. memoria del usuario).
        """
        system_content = cls.system_prompt
        if extra_system_context:
            system_content = system_content + "\n\n" + extra_system_context
        messages = [Message(role="system", content=system_content)]
        messages.extend(history[-10:])  # Últimos 10 mensajes del historial
        messages.append(Message(role="user", content=user_message))
        return messages

    @classmethod
    async def respond(
        cls,
        user_message: str,
        history: List[Message] = None,
        temperature: float = 0.7,
        extra_system_context: str = "",
    ) -> dict:
        """Respuesta completa (no streaming)."""
        messages = cls.build_messages(user_message, history or [], extra_system_context)
        return await chat_completion(
            messages=messages,
            tier=cls.preferred_tier,
            temperature=temperature,
        )

    @classmethod
    async def stream(
        cls,
        user_message: str,
        history: List[Message] = None,
        temperature: float = 0.7,
        extra_system_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """Respuesta en streaming."""
        messages = cls.build_messages(user_message, history or [], extra_system_context)
        async for chunk in chat_stream(
            messages=messages,
            tier=cls.preferred_tier,
            temperature=temperature,
        ):
            yield chunk
