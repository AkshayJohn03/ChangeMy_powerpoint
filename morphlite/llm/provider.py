"""LLM provider abstraction with Azure OpenAI (Entra-ID / API-key) + offline mock.

The provider is config-driven via env vars.  All imports from ``openai`` /
``azure-identity`` are lazy: the rest of morphlite (renderer, content model)
stays usable even when no LLM key is present, with the mock provider as the
fallback.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)

# --- configuration ----------------------------------------------------------

_ENV = os.environ.get

DEFAULT_DEPLOYMENT = _ENV("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
DEFAULT_API_VERSION = _ENV("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

DEFAULT_SYSTEM = (
    "You are a presentation design assistant. You are given the content of a "
    "raw corporate PPTX deck and asked to produce a typed JSON slide spec. "
    "Output ONLY valid JSON matching the requested schema."
)


class ProviderConfig:
    def __init__(self) -> None:
        # Azure OpenAI
        self.endpoint: str = _ENV("AZURE_OPENAI_ENDPOINT", "")
        self.api_key: str = _ENV("AZURE_OPENAI_API_KEY", "")
        self.deployment: str = DEFAULT_DEPLOYMENT
        self.api_version: str = DEFAULT_API_VERSION

        # Any OpenAI-compatible provider (Groq, OpenRouter, Azure via azure.com, etc.)
        self.openai_base_url: str = _ENV("OPENAI_BASE_URL", "")
        self.openai_api_key: str = _ENV("OPENAI_API_KEY", "")

        # Provider allowlist: comma-separated prefixes / substrings of
        # permissible base URLs.  When set, calls to any provider whose
        # base_url does NOT match any entry are blocked (guards against
        # data exfiltration via user-prompt injection).
        allowlist_raw = _ENV("LLM_ALLOWED_ENDPOINTS", "")
        self.allowed_endpoints: list[str] = [
            s.strip() for s in allowlist_raw.split(",") if s.strip()
        ]

        self.model: str = _ENV("LLM_MODEL", _ENV("OPENAI_MODEL", "gpt-4o"))
        self.temperature: float = float(_ENV("LLM_TEMPERATURE", "0.2"))

        self.azure_ad_tenant: str = _ENV("AZURE_AD_TENANT_ID", "")
        self.use_device_code: bool = _ENV("AZURE_USE_DEVICE_CODE", "").lower() in {"1", "true", "yes"}

    def llm_is_configured(self) -> bool:
        return bool(self.endpoint or self.openai_base_url)

    def validate_allowlist(self, url: str) -> bool:
        if not self.allowed_endpoints:
            return True
        return any(a in url for a in self.allowed_endpoints)

    def pick_provider(self, explicit: str = "") -> str:
        """Return one of ``azure``, ``openai``, ``mock``."""
        if explicit:
            return explicit
        if self.endpoint:
            return "azure"
        if self.openai_base_url:
            return "openai"
        return "mock"


CONFIG = ProviderConfig()


# --- base -------------------------------------------------------------------

class BaseLLM(ABC):
    @abstractmethod
    def complete_json(self, messages: list[dict[str, str]], schema_hint: str = "") -> dict:
        ...

    def close(self) -> None:
        pass


# --- mock -------------------------------------------------------------------

_RULE_BASED_ARCHETYPES = [
    ("agenda", "agenda"),
    ("who we are", "content_columns"),
    ("case stud", "content_columns"),
    ("thank", "thank_you"),
    ("network engineering", "card_grid"),
]


class MockLLM(BaseLLM):
    def complete_json(self, messages: list[dict[str, str]], schema_hint: str = "") -> dict:
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        slides_out: list[dict] = []
        import re
        slide_chunks = re.split(r"(?=---\s*slide\s+\d)", user_msg)
        for chunk in slide_chunks:
            chunk = chunk.strip()
            if not chunk or "--- slide" not in chunk.lower():
                continue
            chunk_low = chunk.lower()
            archetype = "generic"
            for kw, arch in _RULE_BASED_ARCHETYPES:
                if kw in chunk_low:
                    archetype = arch
                    break
            # first slide without keyword -> title
            m_idx = re.search(r"---\s*slide\s+(\d+)", chunk)
            slide_no = int(m_idx.group(1)) if m_idx else 0
            if slide_no == 1 and archetype == "generic":
                archetype = "title"
            bullet_lines = []
            for line in chunk.split("\n"):
                line = line.strip()
                if line.startswith("[") and "] " in line:
                    txt = line.split("] ", 1)[1].strip()
                    if txt and txt != "1" and not txt.isdigit():
                        bullet_lines.append(txt)
            title = bullet_lines[0] if bullet_lines else ""
            subtitle = bullet_lines[1] if len(bullet_lines) > 1 else ""
            # keep subtitle separate so title slide can use it
            cards = []
            start = 2 if len(bullet_lines) > 1 and subtitle else 1
            for b in bullet_lines[start:]:
                if b.strip():
                    cards.append({"title": b[:70], "body": [b]})
            # subtitle only for title slide; other slides keep it empty and put all in elements
            out_subtitle = subtitle if archetype == "title" else ""
            if archetype != "title" and subtitle:
                cards.insert(0, {"title": subtitle[:70], "body": [subtitle]})
            slides_out.append(
                {
                    "archetype": archetype,
                    "source_slide": slide_no,
                    "title": title,
                    "subtitle": out_subtitle,
                    "elements": cards,
                    "steps": [],
                    "table": None,
                    "images": [],
                }
            )
        return {"brand": "akkodis", "layout": "16:9", "slides": slides_out}


# --- azure ------------------------------------------------------------------

class AzureLLM(BaseLLM):
    def __init__(self, cfg: ProviderConfig = CONFIG) -> None:
        if not cfg.validate_allowlist(cfg.endpoint):
            raise RuntimeError(
                f"Azure endpoint {cfg.endpoint} not in allowlist "
                f"({cfg.allowed_endpoints})"
            )
        self.cfg = cfg
        self._client = self._build_client()

    def _build_client(self):  # noqa: ANN202
        if self.cfg.api_key:
            import openai
            return openai.AzureOpenAI(
                api_key=self.cfg.api_key,
                azure_endpoint=self.cfg.endpoint,
                api_version=self.cfg.api_version,
            )

        # Entra ID: device-code interactive auth (requires azure-identity)
        try:
            from azure.identity import DefaultAzureCredential, DeviceCodeCredential
        except ImportError:
            raise RuntimeError(
                "Azure OpenAI Entra-ID auth requires `azure-identity`.  "
                "Run: pip install azure-identity"
            )
        import openai

        if self.cfg.use_device_code:
            credential = DeviceCodeCredential(
                tenant_id=self.cfg.azure_ad_tenant or None,
                client_id="04b07795-cd1a-4e8d-8f08-5a8b23c92fc0",
            )
        else:
            credential = DefaultAzureCredential()

        return openai.AzureOpenAI(
            azure_ad_token=credential,
            azure_endpoint=self.cfg.endpoint,
            api_version=self.cfg.api_version,
        )

    def complete_json(self, messages: list[dict[str, str]], schema_hint: str = "") -> dict:
        resp = self._client.chat.completions.create(
            model=self.cfg.deployment,
            messages=messages,
            temperature=self.cfg.temperature,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        return json.loads(raw)

    def close(self) -> None:
        self._client.close()


# --- openai-compatible ------------------------------------------------------

class OpenAILLM(BaseLLM):
    def __init__(self, cfg: ProviderConfig = CONFIG) -> None:
        if not cfg.validate_allowlist(cfg.openai_base_url):
            raise RuntimeError(
                f"Provider {cfg.openai_base_url} not in allowlist {cfg.allowed_endpoints}"
            )
        self.cfg = cfg
        import openai
        self._client = openai.OpenAI(
            api_key=cfg.openai_api_key,
            base_url=cfg.openai_base_url,
        )

    def complete_json(self, messages: list[dict[str, str]], schema_hint: str = "") -> dict:
        resp = self._client.chat.completions.create(
            model=self.cfg.model,
            messages=messages,
            temperature=self.cfg.temperature,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        return json.loads(raw)

    def close(self) -> None:
        self._client.close()


# --- factory ----------------------------------------------------------------

def get_provider(name: str = "", cfg: ProviderConfig = CONFIG) -> BaseLLM:
    """Resolve and return an LLM provider.

    Returns the ``MockLLM`` if no credentials are configured, which lets the
    full pipeline run for end-to-end dev/test without a real key.
    """
    resolved = cfg.pick_provider(name)
    logger.info("LLM provider resolved: %s", resolved)
    if resolved == "azure":
        return AzureLLM(cfg)
    if resolved == "openai":
        return OpenAILLM(cfg)
    logger.warning(
        "No LLM credentials configured (AZURE_OPENAI_ENDPOINT / OPENAI_BASE_URL). "
        "Returning MockLLM."
    )
    return MockLLM()