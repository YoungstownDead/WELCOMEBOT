"""Utilities for interacting with the configured GPT provider."""
from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI

GPT_API_KEY = os.getenv("GPT_API_KEY")
DEFAULT_GPT_MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
DEFAULT_SYSTEM_PROMPT = os.getenv(
    "GPT_SYSTEM_PROMPT",
    "You are a polite and helpful assistant.",
)

_openai_client: Optional[AsyncOpenAI] = (
    AsyncOpenAI(api_key=GPT_API_KEY) if GPT_API_KEY else None
)


def get_openai_client() -> Optional[AsyncOpenAI]:
    """Return the shared AsyncOpenAI client if it is configured."""
    return _openai_client


def gpt_is_configured() -> bool:
    """Indicate whether a GPT API key was supplied."""
    return _openai_client is not None


async def request_chat_completion(
    prompt: str,
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: Optional[str] = None,
) -> str:
    """Request a chat completion for the provided prompt.

    Args:
        prompt: The user prompt to relay to GPT.
        system_prompt: Optional system prompt to prime the model.
        model: Override the default model name, if desired.

    Returns:
        The trimmed content of the first message choice.

    Raises:
        RuntimeError: If no API key is configured.
        Any exception surfaced by the OpenAI SDK when making the request.
    """

    client = get_openai_client()
    if client is None:
        raise RuntimeError("No GPT API key configured.")

    response = await client.chat.completions.create(
        model=model or DEFAULT_GPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    message = response.choices[0].message.content if response.choices else ""
    return message.strip()
