"""Universal LLM caller — supports OpenAI, Anthropic, and Gemini.

Model names are read from environment variables so they can be changed
without touching source code:
    KYROS_OPENAI_MODEL      (default: gpt-4o)
    KYROS_ANTHROPIC_MODEL   (default: claude-3-5-sonnet-20241022)
    KYROS_GEMINI_MODEL      (default: gemini-1.5-flash)
    KYROS_MISTRAL_MODEL     (default: mistral-large-2512)
"""

from __future__ import annotations

import os
import asyncio
import time
import json

import httpx

from kyros.logging import get_logger
from kyros.config import get_settings

logger = get_logger("kyros.ml.models")

# Global rate limiter to prevent "Gemini rate limit exceeded"
# Ensures at least 0.5 seconds between LLM calls
_llm_rate_limit_lock = asyncio.Lock()
_llm_execution_lock = asyncio.Lock()
_last_llm_call_time = 0.0
_LLM_MIN_DELAY = 2.0

# Persistent counter for benchmark tracking
_STATS_FILE = "benchmark_stats.json"

def _load_stats() -> int:
    if os.path.exists(_STATS_FILE):
        try:
            with open(_STATS_FILE, "r") as f:
                data = json.load(f)
                return data.get("total_llm_calls", 0)
        except Exception:
            return 0
    return 0

def _save_stats(count: int) -> None:
    try:
        with open(_STATS_FILE, "w") as f:
            json.dump({"total_llm_calls": count, "last_updated": time.time()}, f)
    except Exception:
        pass

_global_llm_call_count = _load_stats()

# Global callback for tracing (used by benchmarks)
_llm_trace_callback = None

def set_llm_trace_callback(callback):
    global _llm_trace_callback
    _llm_trace_callback = callback

class LLMError(Exception):
    """Raised when an LLM call fails."""


def _openai_model() -> str:
    settings = get_settings()
    return settings.openai_model


def _anthropic_model() -> str:
    settings = get_settings()
    return settings.anthropic_model


def _gemini_model() -> str:
    settings = get_settings()
    return settings.gemini_model


def _mistral_model() -> str:
    settings = get_settings()
    return settings.mistral_model


def get_active_model() -> str:
    """Returns the name of the active model being used based on configured API keys."""
    settings = get_settings()
    if settings.mistral_api_key:
        return _mistral_model()
    elif settings.gemini_api_key:
        return _gemini_model()
    elif settings.openai_api_key:
        return _openai_model()
    elif settings.anthropic_api_key:
        return _anthropic_model()
    return "unknown-model"


def get_global_llm_call_count() -> int:
    """Returns the total number of LLM calls made in the current process."""
    return _global_llm_call_count


async def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.0,
    provider: str | None = None,
    timeout: float = 60.0,
) -> str:
    """Universal LLM caller with integrated rate limiting and persistent retries.
    
    This function will automatically retry on rate limits and transient errors
    until the request is successfully completed.
    """
    global _last_llm_call_time, _global_llm_call_count
    
    async with _llm_execution_lock:
        attempt = 0
        while True:
            attempt += 1
            
            # 1. Pre-emptive Rate Limiting (Internal)
            async with _llm_rate_limit_lock:
                now = time.monotonic()
                elapsed = now - _last_llm_call_time
                if elapsed < _LLM_MIN_DELAY:
                    delay = _LLM_MIN_DELAY - elapsed
                    logger.info(f"Rate limiting LLM call, sleeping for {delay:.2f}s")
                    print(f"      [LLM] Rate limiting LLM call, sleeping for {delay:.2f}s")
                    if _llm_trace_callback:
                        _llm_trace_callback("LLM_RATE_LIMIT", f"Sleeping for {delay:.2f}s", {"delay": delay})
                    await asyncio.sleep(delay)
                
                if attempt == 1: # Only count unique calls
                    _global_llm_call_count += 1
                    _save_stats(_global_llm_call_count)

            settings = get_settings()
            
            active_provider = provider
            if not active_provider:
                if settings.mistral_api_key:
                    active_provider = "mistral"
                elif settings.gemini_api_key:
                    active_provider = "gemini"
                elif settings.openai_api_key:
                    active_provider = "openai"
                elif settings.anthropic_api_key:
                    active_provider = "anthropic"
                else:
                    raise LLMError(
                        "No LLM API key found. Set MISTRAL_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."
                    )

            if attempt > 1:
                print(f"      [LLM] Retry attempt #{attempt} for {active_provider}...")

            logger.info(f"--- Calling LLM Provider: {active_provider} ---")
            print(f"      [LLM] Calling Provider: {active_provider}")
            if _llm_trace_callback:
                _llm_trace_callback("LLM_CALL", f"Calling {active_provider} (Attempt {attempt})", {"provider": active_provider, "prompt_preview": prompt[:100]})
            
            start_time = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if active_provider == "mistral":
                        res = await _call_mistral(client, prompt, system_prompt, temperature)
                    elif active_provider == "openai":
                        res = await _call_openai(client, prompt, system_prompt, temperature)
                    elif active_provider == "gemini":
                        res = await _call_gemini(client, prompt, system_prompt)
                    elif active_provider == "anthropic":
                        res = await _call_anthropic(client, prompt, system_prompt, temperature)
                    else:
                        raise LLMError(f"Unsupported provider: {active_provider!r}")
                    
                    duration = (time.perf_counter() - start_time) * 1000
                    logger.info(f"--- LLM Response Received ({duration:.2f}ms) ---")
                    snippet = res.replace('\n', ' ')[:100] + "..." if len(res) > 100 else res.replace('\n', ' ')
                    print(f"      [LLM] Response Received ({duration:.2f}ms): {snippet}")
                    if _llm_trace_callback:
                        _llm_trace_callback("LLM_RESPONSE", f"Received response from {active_provider}", {"duration_ms": duration, "response": res})
                    _last_llm_call_time = time.monotonic()
                    return res

            except LLMError as e:
                err_str = str(e).lower()
                # If it's a fatal error (Auth, Bad Request), raise immediately
                if any(x in err_str for x in ["api key is invalid", "bad request", "unsupported provider", "lacks permissions"]):
                    print(f"      [LLM FATAL ERROR] {str(e)}")
                    raise
                
                # If it's a rate limit or server error, wait and retry
                wait_time = 20.0 if "rate limit" in err_str else 5.0
                print(f"      [LLM RETRYABLE ERROR] {str(e)}. Retrying in {wait_time}s...")
                if _llm_trace_callback:
                    _llm_trace_callback("LLM_RETRY", f"Retrying due to error: {e}", {"attempt": attempt, "wait": wait_time})
                await asyncio.sleep(wait_time)
                continue

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                wait_time = 10.0
                print(f"      [LLM NETWORK ERROR] {str(e)}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue

            except Exception as e:
                print(f"      [LLM UNEXPECTED ERROR] {str(e)}. Retrying in 5.0s...")
                await asyncio.sleep(5.0)
                continue


async def _call_mistral(
    client: httpx.AsyncClient,
    prompt: str,
    system_prompt: str,
    temperature: float,
) -> str:
    settings = get_settings()
    api_key = os.getenv("MISTRAL_API_KEY") or settings.mistral_api_key
    if not api_key:
        raise LLMError("MISTRAL_API_KEY is not set")

    resp = await client.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": _mistral_model(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        },
    )

    if resp.status_code == 401:
        raise LLMError("Mistral API key is invalid or expired")
    if resp.status_code == 429:
        raise LLMError("Mistral rate limit exceeded — retry after a moment")
    if resp.status_code >= 500:
        raise LLMError(f"Mistral server error ({resp.status_code})")
    if resp.status_code != 200:
        raise LLMError(f"Mistral returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Mistral response shape: {e}") from e


async def _call_openai(
    client: httpx.AsyncClient,
    prompt: str,
    system_prompt: str,
    temperature: float,
) -> str:
    settings = get_settings()
    api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
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
    settings = get_settings()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or settings.gemini_api_key
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not set")

    model = _gemini_model()
    resp = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        json={"contents": [{"parts": [{"text": f"{system_prompt}\n\nUser: {prompt}"}]}]},
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
    settings = get_settings()
    api_key = os.getenv("ANTHROPIC_API_KEY") or settings.anthropic_api_key
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
