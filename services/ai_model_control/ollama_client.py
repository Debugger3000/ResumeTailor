import os
from ollama import AsyncClient
from const.ai_models import ModelProvider
from typing import Optional

# ---
# Ollama info
# ---

class OllamaClient:
    """Wrapper around ollama.AsyncClient with mutable host/model state."""

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host
        self.model = model
        self._client = AsyncClient(host=host) if host else AsyncClient()

    # --- configuration ---

    def set_host(self, host: str) -> None:
        """Swap the underlying client to point at a new host."""
        self.host = host
        self._client = AsyncClient(host=host)

    def set_model(self, model: str) -> None:
        self.model = model

    def configure(self, provider: dict) -> None:
        """Set host + model from a ModelProvider-style dict in one call."""
        host = provider.get("host")
        model = provider.get("model_name")
        if host and host != self.host:
            self.set_host(host)
        if model:
            self.set_model(model)

    @property
    def client(self) -> AsyncClient:
        return self._client

    # --- usage ---

    async def chat(self, messages: list[dict], model: Optional[str] = None, **kwargs) -> str:
        """Send messages, return the assistant's text reply."""
        use_model = model or self.model
        if not use_model:
            raise ValueError("No model set. Call set_model() or pass model=...")
        response = await self._client.chat(model=use_model, messages=messages, **kwargs)
        return response["message"]["content"]

    # async def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
    #     use_model = model or self.model
    #     if not use_model:
    #         raise ValueError("No model set.")
    #     response = await self._client.generate(model=use_model, prompt=prompt, **kwargs)
    #     return response["response"]


# Module-level singleton — import this anywhere
ollama_client = OllamaClient()
