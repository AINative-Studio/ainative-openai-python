"""
ainative-openai — Drop-in replacement for the OpenAI Python SDK.

Routes to AINative's free API with auto-provisioning.

Usage:

    from ainative_openai import OpenAI

    client = OpenAI()  # auto-provisions a free API key
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[{"role": "user", "content": "Hello!"}],
    )

Async usage:

    from ainative_openai import AsyncOpenAI

    client = AsyncOpenAI()
    response = await client.chat.completions.create(...)
"""

from ainative_openai.client import API_BASE, AsyncOpenAI, OpenAI
from ainative_openai.provision import provision

__version__ = "0.1.0"
__all__ = ["OpenAI", "AsyncOpenAI", "provision", "API_BASE", "__version__"]
