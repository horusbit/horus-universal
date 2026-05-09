"""
Agente dinámico — creado en tiempo de ejecución para agentes personalizados de usuario.
A diferencia de los agentes fijos que usan class methods, este usa instance methods
para poder configurar system_prompt y modelo por agente.
"""
from typing import AsyncGenerator, List
from models.schemas import Message
from services.openrouter import chat_completion, chat_stream


class DynamicAgent:
    """
    Agente configurable en runtime para agentes personalizados.
    Recibe system_prompt y model como parámetros del constructor.
    """
    def __init__(self, name: str, emoji: str, system_prompt: str, model: str):
        self.name = name
        self.emoji = emoji
        self.system_prompt = system_prompt
        self.model = model  # e.g. "google/gemini-flash-1.5"

    def _build_messages(
        self,
        user_message: str,
        history: List[Message],
        extra_system_context: str = "",
    ) -> List[Message]:
        system_content = self.system_prompt
        if extra_system_context:
            system_content = system_content + extra_system_context
        messages = [Message(role="system", content=system_content)]
        messages.extend(history[-10:])
        messages.append(Message(role="user", content=user_message))
        return messages

    async def respond(
        self,
        user_message: str,
        history: List[Message] = None,
        temperature: float = 0.7,
        extra_system_context: str = "",
    ) -> dict:
        """Respuesta completa con el modelo y prompt personalizado."""
        messages = self._build_messages(user_message, history or [], extra_system_context)
        return await chat_completion(
            messages=messages,
            model=self.model,
            temperature=temperature,
        )

    async def stream(
        self,
        user_message: str,
        history: List[Message] = None,
        temperature: float = 0.7,
        extra_system_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """Streaming con el modelo y prompt personalizado."""
        messages = self._build_messages(user_message, history or [], extra_system_context)
        async for chunk in chat_stream(
            messages=messages,
            model=self.model,
            temperature=temperature,
        ):
            yield chunk
