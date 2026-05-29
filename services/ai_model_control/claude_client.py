# ai/clients/claude_client.py
import os
from anthropic import AsyncAnthropic


class ClaudeClient:
    def __init__(self):
        self._client: AsyncAnthropic | None = None
        self.model: str | None = None

    def configure(self, model: dict) -> None:
        self.model = model.get("model_name")
        api_key = model.get("api_key_env")
        if not api_key:
            raise RuntimeError("No Anthropic API key set (ANTHROPIC_API_KEY)")
        if not self.model:
            raise RuntimeError("model_config.model_name is not set")
        self._client = AsyncAnthropic(api_key=api_key)

    async def chat(self, messages, schema=None, temperature=0.0, max_tokens=4096):
        if self._client is None:
            raise RuntimeError("Claude client not configured")

        # Anthropic takes the system prompt as a top-level arg, NOT a message role
        system = None
        convo = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                convo.append({"role": m["role"], "content": m["content"]})

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": convo,
        }
        if system:
            kwargs["system"] = system

        # Structured output (your Ollama `format=SCHEMA` equivalent)
        if schema is not None:
            kwargs["tools"] = [{
                "name": "respond",
                "description": "Return the structured result.",
                "input_schema": schema,
            }]
            kwargs["tool_choice"] = {"type": "tool", "name": "respond"}
            resp = await self._client.messages.create(**kwargs)
            for block in resp.content:
                if block.type == "tool_use":
                    return block.input          # dict already matching schema
            raise RuntimeError("Model did not return structured output")

        resp = await self._client.messages.create(**kwargs)
        return "".join(b.text for b in resp.content if b.type == "text")


claude_client = ClaudeClient()