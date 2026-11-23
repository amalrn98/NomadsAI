"""Chat orchestration for NomadsAI.

Persistent memory is intentionally not implemented here. Do not use client-provided
identifiers as user identity. Restore account memory only behind verified auth.
"""

from collections.abc import AsyncGenerator
from typing import Any

from .llm_provider import stream_completion


class AIAgent:
    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        destination: str | None = None,
    ) -> AsyncGenerator[str, None]:
        if not messages or messages[-1].get("role") != "user":
            raise ValueError("The conversation must end with a user message.")

        system_prompt = (
            "You are NomadAI, a practical AI travel assistant. "
            "Distinguish verified facts from estimates. Do not invent current prices, "
            "opening hours, availability, or live travel conditions. If information "
            "may have changed, say that it needs verification."
        )
        if destination:
            system_prompt += f" The user's current destination context is {destination}."

        enhanced_messages = [{"role": "system", "content": system_prompt}, *messages]
        async for chunk in stream_completion(enhanced_messages, temperature=0.7, max_output_tokens=2048):
            yield chunk


ai_agent = AIAgent()
