import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator

import anthropic
import httpx
from google import genai
from google.genai import errors as genai_errors

from services.observability import trace_generation

logger = logging.getLogger(__name__)

# Exceptions that indicate a provider is unavailable (not a programming error).
# genai_errors.APIError is the base for Gemini ServerError (503 overloaded) /
# ClientError, so a transient Gemini failure triggers fallback instead of a raw traceback.
_PROVIDER_ERRORS = (
    httpx.ConnectError,
    httpx.TimeoutException,
    httpx.HTTPStatusError,
    anthropic.APIError,
    genai_errors.APIError,
    ConnectionError,
    TimeoutError,
)


def _gemini_usage(response) -> dict:
    """Best-effort extraction of token usage from a Gemini response/chunk."""
    meta = getattr(response, "usage_metadata", None) if response is not None else None
    if meta is None:
        return {}
    return {
        "input_tokens": getattr(meta, "prompt_token_count", None) or 0,
        "output_tokens": getattr(meta, "candidates_token_count", None) or 0,
    }


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str: ...

    @abstractmethod
    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]: ...


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        with trace_generation("claude.generate", self.model, prompt) as gen:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system or "You are a helpful research assistant.",
                messages=[{"role": "user", "content": prompt}],
            )
            if not response.content:
                raise ValueError("Claude returned an empty response")
            text = response.content[0].text
            if gen is not None:
                gen.update(
                    output=text,
                    usage_details={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                )
            return text

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        with trace_generation("claude.stream", self.model, prompt) as gen:
            chunks: list[str] = []
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system or "You are a helpful research assistant.",
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    chunks.append(text)
                    yield text
                if gen is not None:
                    try:
                        final = await stream.get_final_message()
                        gen.update(
                            output="".join(chunks),
                            usage_details={
                                "input_tokens": final.usage.input_tokens,
                                "output_tokens": final.usage.output_tokens,
                            },
                        )
                    except Exception:
                        gen.update(output="".join(chunks))


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        with trace_generation("gemini.generate", self.model, prompt) as gen:
            response = await asyncio.to_thread(
                self.client.models.generate_content, model=self.model, contents=full_prompt
            )
            if response.text is None:
                raise ValueError("Gemini returned an empty response (possibly blocked by safety filters)")
            if gen is not None:
                gen.update(output=response.text, usage_details=_gemini_usage(response))
            return response.text

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        with trace_generation("gemini.stream", self.model, prompt) as gen:
            response_iter = await asyncio.to_thread(
                self.client.models.generate_content_stream, model=self.model, contents=full_prompt
            )

            def _next_chunk(it):
                """Pull one chunk from the sync iterator (runs in a thread)."""
                return next(it, None)

            chunks: list[str] = []
            last_chunk = None
            while True:
                chunk = await asyncio.to_thread(_next_chunk, response_iter)
                if chunk is None:
                    break
                last_chunk = chunk
                if chunk.text:
                    chunks.append(chunk.text)
                    yield chunk.text
            if gen is not None:
                gen.update(output="".join(chunks), usage_details=_gemini_usage(last_chunk))


class FallbackLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    async def generate(self, prompt: str, system: str = "") -> str:
        try:
            return await self.primary.generate(prompt, system)
        except _PROVIDER_ERRORS as e:
            logger.warning("Primary LLM provider failed, falling back: %s", e)
            return await self.fallback.generate(prompt, system)

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        try:
            async for token in self.primary.stream(prompt, system):
                yield token
        except _PROVIDER_ERRORS as e:
            logger.warning("Primary LLM provider failed during stream, falling back: %s", e)
            async for token in self.fallback.stream(prompt, system):
                yield token
