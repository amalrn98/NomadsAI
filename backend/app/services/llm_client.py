"""Synchronous Gemini client for legacy synchronous service call sites."""

import os
from typing import Any

import httpx

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def is_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _to_gemini(messages: list[dict[str, str]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    system_parts: list[str] = []
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
    instruction = {"parts": [{"text": "\n\n".join(system_parts)}]} if system_parts else None
    return instruction, contents


def chat(
    messages: list[dict[str, str]],
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """Generate text with the server-configured Gemini key.

    Legacy base_url/api_key parameters are intentionally ignored. Clients cannot
    select arbitrary upstream hosts or supply credentials to the backend.
    """
    del base_url, api_key
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Gemini is not configured. Set GEMINI_API_KEY on the backend.")

    instruction, contents = _to_gemini(messages)
    if not contents:
        raise ValueError("At least one user message is required.")

    payload: dict[str, Any] = {"contents": contents}
    if instruction:
        payload["systemInstruction"] = instruction
    selected_model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    url = f"{GEMINI_API_BASE}/{selected_model}:generateContent"

    with httpx.Client(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates") or []
    if not candidates:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "unknown")
        raise RuntimeError(f"Gemini returned no response candidate (reason: {reason}).")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    result = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not result:
        raise RuntimeError("Gemini returned an empty text response.")
    return result


def get_ai_provider_info() -> dict[str, Any]:
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    return {
        "gemini": {
            "name": "Google Gemini",
            "status": "configured" if is_configured() else "not_configured",
            "model": model,
            "capabilities": ["text generation", "multi-turn chat", "system instructions"],
        }
    }
