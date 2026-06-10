"""
Drop-in replacements for ``openai.OpenAI`` and ``openai.AsyncOpenAI``.

These subclasses default to the AINative API and auto-provision a free
API key when none is supplied:

    from ainative_openai import OpenAI

    client = OpenAI()  # auto-provisions key, routes to AINative
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[{"role": "user", "content": "Hello!"}],
    )
"""

from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI as _AsyncOpenAI
from openai import OpenAI as _OpenAI

from ainative_openai.provision import load_saved_key, provision

API_BASE = "https://api.ainative.studio/api/v1"
_SDK_VERSION = "0.1.0"


def _resolve_key(api_key: Optional[str]) -> str:
    """
    Resolve an API key through the priority chain:

    1. Explicit ``api_key`` argument
    2. ``AINATIVE_API_KEY`` env var
    3. ``OPENAI_API_KEY`` env var
    4. Saved key in ``~/.ainative/config.json``
    5. Auto-provision via instant-db
    """
    if api_key:
        return api_key

    env_key = os.environ.get("AINATIVE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key

    saved = load_saved_key()
    if saved:
        return saved

    return provision()


class OpenAI(_OpenAI):
    """
    AINative-flavored OpenAI client.

    Works exactly like ``openai.OpenAI`` but defaults ``base_url`` to the
    AINative API and auto-provisions a free API key when none is provided.

    All models supported by AINative (Llama, Qwen, DeepSeek, Kimi) are
    available through the standard OpenAI chat completions interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        key = _resolve_key(api_key)
        url = base_url or os.environ.get("AINATIVE_BASE_URL", API_BASE)

        # Inject SDK identification header for telemetry
        default_headers = kwargs.pop("default_headers", {})
        default_headers.setdefault("X-SDK", f"ainative-openai-python/{_SDK_VERSION}")

        super().__init__(
            api_key=key, base_url=url, default_headers=default_headers, **kwargs
        )


class AsyncOpenAI(_AsyncOpenAI):
    """
    Async variant of the AINative-flavored OpenAI client.

    Works exactly like ``openai.AsyncOpenAI`` but defaults ``base_url`` to
    the AINative API and auto-provisions a free API key when none is provided.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        key = _resolve_key(api_key)
        url = base_url or os.environ.get("AINATIVE_BASE_URL", API_BASE)

        default_headers = kwargs.pop("default_headers", {})
        default_headers.setdefault("X-SDK", f"ainative-openai-python/{_SDK_VERSION}")

        super().__init__(
            api_key=key, base_url=url, default_headers=default_headers, **kwargs
        )
