"""Universal LLM caller — supports OpenAI, Anthropic, and Gemini.

Model names are read from environment variables so they can be changed
without touching source code:
    KYROS_OPENAI_MODEL      (default: gpt-4o)
    KYROS_ANTHROPIC_MODEL   (default: claude-3-5-sonnet-20241022)
    KYROS_GEMINI_MODEL      (default: gemini-1.5-flash)
"""

from __future__ import annotations

import os

import httpx

from kyros.logging import get_logger

logger = get_logger("kyros.ml.models")


class LLMError(Exception):
    """Raised when an LLM call fails."""


def _openai_model() -> str:
    return os.environ.get("KYROS_OPENAI_MODEL", "gpt-4o")


def _anthropic_model() -> str:
    return os.environ.get("KYROS_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


def _gemini_model() -> str:
    return os.environ.get("KYROS_GEMINI_MODEL", "gemini-1.5-flash")


async def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.1,
    provider: str | None = None,
    timeout: float = 60.0,
) -> str:
    """Universal LLM caller. Auto-detects provider from available API keys.

    Args:
        prompt: The user prompt to send.
        system_prompt: System-level instruction for the model.
        temperature: Sampling temperature (0.0 = deterministic).
        provider: Force a specific provider. Auto-detected from env if None.
        timeout: HTTP request timeout in seconds.

    Raises:
        LLMError: If no provider is configured or the API call fails.
    """
    if not provider:
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            provider = "gemini"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            raise LLMError(
                "No LLM API key found. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY."
            )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider == "openai":
                return await _call_openai(client, prompt, system_prompt, temperature)
            elif provider == "gemini":
                return await _call_gemini(client, prompt, system_prompt)
            elif provider == "anthropic":
                return await _call_anthropic(client, prompt, system_prompt, temperature)
            else:
                raise LLMError(f"Unsupported provider: {provider!r}")
    except LLMError:
        raise
    except httpx.TimeoutException as e:
        logger.error("LLM request timed out", provider=provider, timeout=timeout)
        raise LLMError(f"LLM request timed out after {timeout}s") from e
    except httpx.ConnectError as e:
        logger.error("LLM connection failed", provider=provider, error=str(e))
        raise LLMError(f"Could not connect to {provider} API") from e
    except Exception as e:
        logger.error("Unexpected LLM error", provider=provider, error=str(e))
        raise LLMError(f"LLM call failed: {e}") from e


async def _call_openai(
    client: httpx.AsyncClient,
    prompt: str,
    system_prompt: str,
    temperature: float,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set")

    resp = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": _openai_model(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        },
    )

    if resp.status_code == 401:
        raise LLMError("OpenAI API key is invalid or expired")
    if resp.status_code == 429:
        raise LLMError("OpenAI rate limit exceeded — retry after a moment")
    if resp.status_code >= 500:
        raise LLMError(f"OpenAI server error ({resp.status_code})")
    if resp.status_code != 200:
        raise LLMError(f"OpenAI returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected OpenAI response shape: {e}") from e


async def _call_gemini(
    client: httpx.AsyncClient,
    prompt: str,
    system_prompt: str,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not set")

    model = _gemini_model()
    resp = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        json={
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\nUser: {prompt}"}]}
            ]
        },
    )

    if resp.status_code == 400:
        raise LLMError(f"Gemini bad request: {resp.text[:200]}")
    if resp.status_code == 403:
        raise LLMError("Gemini API key is invalid or lacks permissions")
    if resp.status_code == 429:
        raise LLMError("Gemini rate limit exceeded — retry after a moment")
    if resp.status_code >= 500:
        raise LLMError(f"Gemini server error ({resp.status_code})")
    if resp.status_code != 200:
        raise LLMError(f"Gemini returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        finish_reason = data.get("candidates", [{}])[0].get("finishReason", "UNKNOWN")
        raise LLMError(f"Gemini response blocked or empty (finishReason={finish_reason})") from e


async def _call_anthropic(
    client: httpx.AsyncClient,
    prompt: str,
    system_prompt: str,
    temperature: float,
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set")

    resp = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": _anthropic_model(),
            "max_tokens": 1024,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    if resp.status_code == 401:
        raise LLMError("Anthropic API key is invalid or expired")
    if resp.status_code == 429:
        raise LLMError("Anthropic rate limit exceeded — retry after a moment")
    if resp.status_code >= 500:
        raise LLMError(f"Anthropic server error ({resp.status_code})")
    if resp.status_code != 200:
        raise LLMError(f"Anthropic returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    try:
        return data["content"][0]["text"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Anthropic response shape: {e}") from e
