"""Optional LLM client factory (env-configured) for copy rewriting.

Env: LLM_API_KEY, LLM_BASE_URL (default OpenAI), LLM_MODEL (default gpt-4o-mini).
Returns None when unconfigured — every caller must treat that as "feature off",
never as an error.
"""

from __future__ import annotations

import os
from typing import Protocol


class LLMClient(Protocol):
    async def complete(self, prompt: str) -> str: ...


def env_client() -> LLMClient | None:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        return None
    base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    class _OpenAICompat:
        async def complete(self, prompt: str) -> str:
            import httpx

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.4,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

    return _OpenAICompat()
