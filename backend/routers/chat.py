"""
Router de Chat - Endpoint principal de HORUS Universal
Con auto-routing inteligente y memoria persistente
"""
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse, Message, AgentType
from agents import get_agent
from services.redis_cache import cache
from services.router import detect_agent, get_routing_message
from services.supabase_db import ensure_conversation_exists, save_message
from auth.supabase_auth import get_optional_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user=Depends(get_optional_user),
):
    """Endpoint de chat sin streaming — con auto-routing."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Auto-routing: detectar agente óptimo
    effective_agent = detect_agent(request.message, request.agent)

    # Obtener historial
    history = await cache.get_conversation(conversation_id)
    if request.history:
        history = request.history

    agent_class = get_agent(effective_agent)
    routing_prefix = get_routing_message(effective_agent, request.agent) or ""

    try:
        result = await agent_class.respond(
            user_message=request.message,
            history=history,
        )

        full_content = routing_prefix + result["content"]
        model_used = result.get("model", "unknown")

        user_msg = Message(role="user", content=request.message)
        assistant_msg = Message(role="assistant", content=full_content)

        # Redis (rápido)
        await cache.append_message(conversation_id, user_msg)
        await cache.append_message(conversation_id, assistant_msg)

        # Supabase (persistente)
        if user:
            await ensure_conversation_exists(conversation_id, user.id, effective_agent.value)
            await save_message(conversation_id, user_msg)
            await save_message(conversation_id, assistant_msg, effective_agent.value, model_used)

        return ChatResponse(
            content=full_content,
            agent=effective_agent,
            model_used=model_used,
            conversation_id=conversation_id,
            tokens_used=result.get("usage", {}).get("total_tokens"),
        )

    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    user=Depends(get_optional_user),
):
    """Endpoint de chat con streaming SSE — con auto-routing."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Auto-routing
    effective_agent = detect_agent(request.message, request.agent)
    routing_prefix = get_routing_message(effective_agent, request.agent)

    # Obtener historial
    history = await cache.get_conversation(conversation_id)
    if request.history:
        history = request.history

    user_msg = Message(role="user", content=request.message)
    await cache.append_message(conversation_id, user_msg)

    # Persistir en Supabase si hay usuario
    if user:
        await ensure_conversation_exists(conversation_id, user.id, effective_agent.value)
        await save_message(conversation_id, user_msg)

    agent_class = get_agent(effective_agent)
    full_response = []

    async def generate():
        nonlocal full_response
        try:
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id, 'agent': effective_agent.value})}\n\n"

            if routing_prefix:
                full_response.append(routing_prefix)
                yield f"data: {json.dumps({'type': 'chunk', 'content': routing_prefix})}\n\n"

            async for chunk in agent_class.stream(
                user_message=request.message,
                history=history,
            ):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            complete_response = "".join(full_response)
            if complete_response:
                assistant_msg = Message(role="assistant", content=complete_response)
                await cache.append_message(conversation_id, assistant_msg)
                if user:
                    await save_message(conversation_id, assistant_msg, effective_agent.value)

            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id, 'agent': effective_agent.value})}\n\n"

        except Exception as e:
            logger.error(f"Error en stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.delete("/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    user=Depends(get_optional_user),
):
    """Limpia el historial de una conversación."""
    await cache.delete_conversation(conversation_id)
    return {"message": "Conversación eliminada", "conversation_id": conversation_id}
