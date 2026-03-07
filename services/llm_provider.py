from abc import ABC, abstractmethod
from typing import AsyncGenerator

import anthropic
from google import genai


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
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system or "You are a helpful research assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system or "You are a helpful research assistant.",
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self.client.models.generate_content(model=self.model, contents=full_prompt)
        return response.text

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        for chunk in self.client.models.generate_content_stream(model=self.model, contents=full_prompt):
            if chunk.text:
                yield chunk.text


class FallbackLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    async def generate(self, prompt: str, system: str = "") -> str:
        try:
            return await self.primary.generate(prompt, system)
        except Exception:
            return await self.fallback.generate(prompt, system)

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        try:
            async for token in self.primary.stream(prompt, system):
                yield token
        except Exception:
            async for token in self.fallback.stream(prompt, system):
                yield token
