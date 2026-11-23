import json
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, model_validator

from ..rate_limit import limiter
from ..services.ai_agent import ai_agent

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class TravelContext(BaseModel):
    destination: str | None = Field(default=None, max_length=160)
    dates: str | None = Field(default=None, max_length=80)
    travelers: int | None = Field(default=None, ge=1, le=20)
    budget: str | None = Field(default=None, max_length=80)
    interests: list[str] = Field(default_factory=list, max_length=10)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    destination: str | None = Field(default=None, max_length=160)
    travel_context: TravelContext | None = None
    stream: bool = False

    @model_validator(mode="after")
    def validate_payload_size(self):
        if sum(len(message.content) for message in self.messages) > 24000:
            raise ValueError("The combined message content must not exceed 24,000 characters.")
        return self

    def resolved_destination(self) -> str | None:
        return self.destination or (self.travel_context.destination if self.travel_context else None)


def _messages(req: ChatRequest) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in req.messages]


def _stream_response(req: ChatRequest) -> StreamingResponse:
    messages = _messages(req)
    destination = req.resolved_destination()

    async def generate():
        try:
            async for chunk in ai_agent.chat_stream(messages=messages, destination=destination):
                yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception:
            logger.exception("Gemini chat stream failed")
            yield f"data: {json.dumps({'error': 'The chat service is temporarily unavailable.', 'type': 'error'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/stream")
@limiter.limit("5/minute")
async def chat_stream_endpoint(request: Request, req: ChatRequest):
    return _stream_response(req)


@router.post("/")
@limiter.limit("8/minute")
async def chat_endpoint(request: Request, req: ChatRequest):
    if req.stream:
        return _stream_response(req)

    try:
        reply = "".join([
            chunk async for chunk in ai_agent.chat_stream(
                messages=_messages(req),
                destination=req.resolved_destination(),
            )
        ])
        if not reply.strip():
            raise RuntimeError("Gemini returned an empty response.")
        return {"reply": reply, "provider": "gemini", "has_memory": False}
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=503,
            detail="The AI chat service is temporarily unavailable. Please try again later.",
        ) from exc
