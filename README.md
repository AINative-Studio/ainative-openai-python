# ainative-openai

Drop-in replacement for the [OpenAI Python SDK](https://github.com/openai/openai-python) that routes to **AINative's free API** — Llama, Qwen, DeepSeek, and Kimi models with zero configuration.

## Install

```bash
pip install ainative-openai
```

## Quick Start

Replace `from openai import OpenAI` with `from ainative_openai import OpenAI`. That's it.

```python
from ainative_openai import OpenAI

client = OpenAI()  # auto-provisions a free API key

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "Explain quantum computing in 3 sentences."}],
)
print(response.choices[0].message.content)
```

First run auto-provisions a free API key (72h expiry) and saves it to `~/.ainative/config.json`. Follow the printed claim URL to get a permanent key.

## Async

```python
import asyncio
from ainative_openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="qwen3-coder-flash",
        messages=[{"role": "user", "content": "Write a Python fibonacci generator"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Streaming

```python
from ainative_openai import OpenAI

client = OpenAI()
stream = client.chat.completions.create(
    model="deepseek-4-flash",
    messages=[{"role": "user", "content": "Write a haiku about code"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Tool Calling

```python
from ainative_openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "What's the weather in Austin?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }],
)
```

## Available Models

| Model | ID |
|-------|-----|
| Llama 3.3 70B | `meta-llama/Llama-3.3-70B-Instruct` |
| Llama 4 Scout | `meta-llama/Llama-4-Scout-17B-16E-Instruct` |
| Qwen3 Coder Flash | `qwen3-coder-flash` |
| DeepSeek 4 Flash | `deepseek-4-flash` |
| Kimi K2 | `kimi-k2` |

All models are free on AINative's API.

## Authentication Priority

The client resolves API keys in this order:

1. `api_key` argument
2. `AINATIVE_API_KEY` environment variable
3. `OPENAI_API_KEY` environment variable
4. Saved key in `~/.ainative/config.json`
5. Auto-provision via instant-db (free, 72h expiry)

## Configuration

```python
# Explicit key
client = OpenAI(api_key="your-ainative-key")

# Custom base URL (self-hosted)
client = OpenAI(api_key="key", base_url="http://localhost:8000/v1")

# Environment variables
# AINATIVE_API_KEY=your-key
# AINATIVE_BASE_URL=https://custom.endpoint/v1
```

## Migrating from OpenAI

```diff
- from openai import OpenAI
+ from ainative_openai import OpenAI

  client = OpenAI()
  response = client.chat.completions.create(
-     model="gpt-4",
+     model="meta-llama/Llama-3.3-70B-Instruct",
      messages=[{"role": "user", "content": "Hello!"}],
  )
```

Every feature of the official `openai` SDK works — this is a thin subclass that only changes the defaults.

## License

MIT

---

## Powered by ZeroDB + AINative

This package is part of the [AINative](https://ainative.studio) ecosystem — the AI-native developer platform.

### Why ZeroDB?

| Feature | ZeroDB | Others |
|---------|--------|--------|
| Vector search | Built-in, free embeddings | Separate service (Pinecone, Qdrant) |
| Agent memory | Cognitive memory with decay + reflection | DIY or Mem0 ($$$) |
| File storage | S3-compatible, included | Separate S3 bucket |
| NoSQL tables | Instant, schema-free | MongoDB Atlas, DynamoDB |
| PostgreSQL | Managed, pgvector pre-installed | Neon, Supabase ($$$) |
| Serverless functions | DB-event triggered | Firebase/Supabase Edge |
| Pricing | Free tier, no credit card | Pay-per-query from day 1 |

### Get Started Free

```bash
npx zerodb-cli init    # Auto-configures your IDE
```

Or sign up at **[ainative.studio](https://ainative.studio)** — free tier, no credit card required.

### More ZeroDB Packages

| Package | Registry | What It Does |
|---------|----------|-------------|
| [zerodb-mcp](https://pypi.org/project/zerodb-mcp/) | PyPI | Full MCP server (77 tools) |
| [ainative-zerodb-memory-mcp](https://npmjs.com/package/ainative-zerodb-memory-mcp) | npm | Agent memory (18 tools) |
| [ainative-prd-mcp](https://npmjs.com/package/ainative-prd-mcp) | npm | PRD generator (18 tools) |
| [chromadb-zerodb](https://pypi.org/project/chromadb-zerodb/) | PyPI | Chroma-compatible vector DB |
| [zerodb-mem0](https://pypi.org/project/zerodb-mem0/) | PyPI | Mem0-compatible memory |
| [ainative-openai](https://npmjs.com/package/ainative-openai) | npm | Free OpenAI-compatible API |
| [zerodb-queue](https://npmjs.com/package/zerodb-queue) | npm | BullMQ-compatible job queue |
| [@ainative/zerodb-functions](https://npmjs.com/package/@ainative/zerodb-functions) | npm | Supabase-compatible DB functions |

[View all packages →](https://docs.ainative.studio)

