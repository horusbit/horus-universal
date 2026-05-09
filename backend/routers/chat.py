"""
Router de Chat - Endpoint principal de HORUS Universal
Con auto-routing inteligente, memoria persistente y límites por plan
"""
import uuid
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse, Message, AgentType
from agents import get_agent
from agents.dynamic import DynamicAgent
from services.redis_cache import cache
from services.router import detect_agent, get_routing_message
from services.supabase_db import ensure_conversation_exists, save_message, get_custom_agent_by_id
from services.usage import check_usage_limit, increment_usage
from services.memory import get_user_memory, extract_and_save_facts, build_memory_context
from services.web_search import needs_web_search, search_web, format_search_context
from auth.supabase_auth import get_optional_user
import logging

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user=Depends(get_optional_user),
):
    """Endpoint de chat sin streaming — con auto-routing y límites de plan."""
    # Verificar límite de uso
    user_email = getattr(user, "email", "") if user else ""
    usage = await check_usage_limit(user, user_email)
    if not usage["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "limit_reached",
                "message": f"Límite diario alcanzado ({usage['limit']} mensajes). Actualiza a Pro para uso ilimitado.",
                "plan": usage["plan"],
                "used": usage["used"],
                "limit": usage["limit"],
            }
        )

    conversation_id = request.conversation_id or str(uuid.uuid4())

    history = await cache.get_conversation(conversation_id)
    if request.history:
        history = request.history

    # Cargar y extraer memoria del usuario
    memory_context = ""
    if user:
        memory = await get_user_memory(user.id)
        memory_context = build_memory_context(memory)
        await extract_and_save_facts(user.id, request.message)

    # Detectar si es un agente personalizado (UUID) o un agente built-in
    agent_id_str = str(request.agent) if request.agent else ""
    custom_agent_data = None
    if UUID_RE.match(agent_id_str):
        custom_agent_data = await get_custom_agent_by_id(agent_id_str)

    try:
        if custom_agent_data:
            # Agente personalizado
            dynamic_agent = DynamicAgent(
                name=custom_agent_data["name"],
                emoji=custom_agent_data["emoji"],
                system_prompt=custom_agent_data["system_prompt"],
                model=custom_agent_data["base_model"],
            )
            result = await dynamic_agent.respond(
                user_message=request.message,
                history=history,
                extra_system_context=memory_context,
            )
            agent_label = custom_agent_data["name"].lower()
            routing_prefix = ""
            effective_agent_value = agent_id_str
        else:
            # Agente built-in
            effective_agent = detect_agent(request.message, request.agent)
            agent_class = get_agent(effective_agent)
            routing_prefix = get_routing_message(effective_agent, request.agent) or ""
            result = await agent_class.respond(
                user_message=request.message,
                history=history,
                extra_system_context=memory_context,
            )
            agent_label = effective_agent.value
            effective_agent_value = effective_agent.value

        full_content = routing_prefix + result["content"]
        model_used = result.get("model", "unknown")

        user_msg = Message(role="user", content=request.message)
        assistant_msg = Message(role="assistant", content=full_content)

        await cache.append_message(conversation_id, user_msg)
        await cache.append_message(conversation_id, assistant_msg)

        if user:
            await ensure_conversation_exists(conversation_id, user.id, effective_agent_value)
            await save_message(conversation_id, user_msg)
            await save_message(conversation_id, assistant_msg, agent_label, model_used)
            await increment_usage(user.id)

        return ChatResponse(
            content=full_content,
            agent=effective_agent if not custom_agent_data else AgentType.atlas,
            model_used=model_used,
            conversation_id=conversation_id,
            tokens_used=result.get("usage", {}).get("total_tokens"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    user=Depends(get_optional_user),
):
    """Endpoint de chat con streaming SSE — con auto-routing y límites de plan."""
    # Verificar límite de uso
    user_email = getattr(user, "email", "") if user else ""
    usage = await check_usage_limit(user, user_email)
    if not usage["allowed"]:
        limit_msg = json.dumps({
            "type": "error",
            "code": "limit_reached",
            "message": f"Límite diario alcanzado ({usage['limit']} mensajes). Actualiza a Pro para uso ilimitado.",
            "plan": usage["plan"],
        })
        async def limit_error():
            yield f"data: {limit_msg}\n\n"
        return StreamingResponse(limit_error(), media_type="text/event-stream")

    conversation_id = request.conversation_id or str(uuid.uuid4())

    history = await cache.get_conversation(conversation_id)
    if request.history:
        history = request.history

    user_msg = Message(role="user", content=request.message)
    await cache.append_message(conversation_id, user_msg)

    # Cargar memoria + persistir mensaje de usuario
    memory_context = ""
    agent_id_str = str(request.agent) if request.agent else ""
    custom_agent_data = None

    if UUID_RE.match(agent_id_str):
        custom_agent_data = await get_custom_agent_by_id(agent_id_str)

    if custom_agent_data:
        effective_agent_label = custom_agent_data["name"].lower()
        effective_agent_value = agent_id_str
        routing_prefix = ""
    else:
        effective_agent = detect_agent(request.message, request.agent)
        effective_agent_label = effective_agent.value
        effective_agent_value = effective_agent.value
        routing_prefix = get_routing_message(effective_agent, request.agent)

    # Búsqueda web automática si el mensaje lo requiere
    web_context = ""
    if needs_web_search(request.message):
        search_results = await search_web(request.message)
        if search_results:
            web_context = format_search_context(search_results, request.message)
            logger.info(f"[WebSearch] Contexto agregado: {len(web_context)} chars")

    if user:
        memory = await get_user_memory(user.id)
        memory_context = build_memory_context(memory)
        await extract_and_save_facts(user.id, request.message)
        await ensure_conversation_exists(conversation_id, user.id, effective_agent_value)
        await save_message(conversation_id, user_msg)
        await increment_usage(user.id)
        # Registrar en Redis por usuario (fallback si Supabase falla)
        await cache.register_user_conversation(user.id, conversation_id)

    # Combinar contextos: memoria + web search
    if web_context:
        memory_context = (web_context + "\n\n" + memory_context).strip()

    full_response = []

    async def generate():
        nonlocal full_response
        try:
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id, 'agent': effective_agent_label})}\n\n"

            if routing_prefix:
                full_response.append(routing_prefix)
                yield f"data: {json.dumps({'type': 'chunk', 'content': routing_prefix})}\n\n"

            if custom_agent_data:
                dynamic_agent = DynamicAgent(
                    name=custom_agent_data["name"],
                    emoji=custom_agent_data["emoji"],
                    system_prompt=custom_agent_data["system_prompt"],
                    model=custom_agent_data["base_model"],
                )
                stream_iter = dynamic_agent.stream(
                    user_message=request.message,
                    history=history,
                    extra_system_context=memory_context,
                )
            else:
                agent_class = get_agent(effective_agent)
                stream_iter = agent_class.stream(
                    user_message=request.message,
                    history=history,
                    extra_system_context=memory_context,
                )

            async for chunk in stream_iter:
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            complete_response = "".join(full_response)
            if complete_response and user:
                assistant_msg = Message(role="assistant", content=complete_response)
                await cache.append_message(conversation_id, assistant_msg)
                await save_message(conversation_id, assistant_msg, effective_agent_label)

            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id, 'agent': effective_agent_label})}\n\n"

        except Exception as e:
            logger.error(f"Error en stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="tex