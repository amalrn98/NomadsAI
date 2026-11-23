"""Gemini API provider used by NomadsAI."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _messages_to_gemini(messages: list[dict[str, str]]) -> tuple[dict[str, str] | None, list[dict[str, Any]]]:
    """Convert OpenAI-style messages to Gemini systemInstruction and contents."""
    system_parts = []
    contents: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = str(message.get("content", ""))
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        if contents and contents[-1]["role"] == gemini_role:
            contents[-1]["parts"].append({"text": content})
        else:
            contents.append({"role": gemini_role, "parts": [{"text": content}]})

    system_instruction = {"parts": [{"text": "\n\n".join(system_parts)}]} if system_parts else None
    return system_instruction, contents


class GeminiProvider:
    """Single-provider Gemini client. Credentials are read from server environment."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_completion(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini is not configured. Set GEMINI_API_KEY on the backend.")

        system_instruction, contents = _messages_to_gemini(messages)
        if not contents:
            raise ValueError("At least one user message is required.")

        payload: dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        generation_config: dict[str, Any] = {}
        if "temperature" in kwargs:
            generation_config["temperature"] = kwargs["temperature"]
        max_tokens = kwargs.get("max_output_tokens", kwargs.get("max_tokens"))
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if generation_config:
            payload["generationConfig"] = generation_config

        model = kwargs.get("model") or self.model
        url = f"{GEMINI_API_BASE}/{model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates") or []
        if not candidates:
            block_reason = (data.get("promptFeedback") or {}).get("blockReason", "unknown")
            raise RuntimeError(f"Gemini returned no response candidate (reason: {block_reason}).")

        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        if not text.strip():
            raise RuntimeError("Gemini returned an empty text response.")
        return text.strip()


_provider: GeminiProvider | None = None


def get_llm_provider() -> GeminiProvider:
    global _provider
    if _provider is None:
        _provider = GeminiProvider()
    return _provider


def is_configured() -> bool:
    return get_llm_provider().is_configured()


async def generate_completion(messages: list[dict[str, str]], **kwargs: Any) -> str:
    return await get_llm_provider().generate_completion(messages, **kwargs)


def get_ai_provider_info() -> dict[str, Any]:
    provider = get_llm_provider()
    return {
        "configured_providers": ["gemini"] if provider.is_configured() else [],
        "default_provider": "gemini",
        "gemini": {
            "name": "Google Gemini",
            "model": provider.model,
            "status": "configured" if provider.is_configured() else "not_configured",
            "priority": "primary",
        },
    }
