import json
import logging
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.ai_agent import ai_agent
from ..services import llm_client
from ..utils.knowledge import load_city_knowledge
from .signals import get_signals

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    destination: Optional[str] = Field(default=None, max_length=160)
    # JSON is the default contract used by the web client. Streaming is opt-in.
    stream: bool = False


class ChatStreamRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    destination: Optional[str] = Field(default=None, max_length=160)


@router.post("/stream")
async def chat_stream_endpoint(req: ChatStreamRequest):
    """Stream a chat response using the server-configured Gemini provider."""
    user_id = str(uuid.uuid4())
    messages = [{"role": message.role, "content": message.content} for message in req.messages]

    async def generate():
        try:
            async for chunk in ai_agent.chat_stream(
                messages=messages,
                user_id=user_id,
                destination=req.destination,
            ):
                yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception:
            logger.exception("Chat stream failed")
            yield f"data: {json.dumps({'error': 'The chat service encountered an error.', 'type': 'error'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/")
async def chat_endpoint(req: ChatRequest):
    """Return a JSON chat response, or an SSE stream when explicitly requested."""
    if req.stream:
        return await chat_stream_endpoint(
            ChatStreamRequest(messages=req.messages, destination=req.destination)
        )

    user_id = str(uuid.uuid4())
    messages = [{"role": message.role, "content": message.content} for message in req.messages]

    try:
        full_response = ""
        async for chunk in ai_agent.chat_stream(
            messages=messages,
            user_id=user_id,
            destination=req.destination,
        ):
            full_response += chunk

        return {
            "reply": full_response,
            "provider": "gemini",
            "has_memory": False,
        }
    except Exception:
        logger.exception("Primary chat flow failed")
        try:
            reply = llm_client.chat(messages)
            return {"reply": reply, "provider": "gemini", "fallback": True}
        except Exception:
            logger.exception("Gemini fallback failed")
            city = req.destination or ""
            knowledge = load_city_knowledge(city) or {}
            signals = await get_signals(destination=city or None, region=None, limit=5)
            parts = []
            if knowledge.get("landmarks"):
                landmarks = ", ".join(item["name"] for item in knowledge["landmarks"][:5])
                parts.append(f"Top landmarks: {landmarks}.")
            if knowledge.get("food"):
                food = ", ".join(item["name"] for item in knowledge["food"][:3])
                parts.append(f"Food experiences: {food}.")
            if signals:
                current = "; ".join(
                    f"{item['type']}: {item.get('title') or item.get('name') or item.get('to')}"
                    for item in signals[:3]
                )
                parts.append(f"Current signals: {current}.")
            answer = " ".join(parts) or "Ask me about a city to get tailored picks."
            return {"reply": answer, "provider": "offline", "fallback": True}
