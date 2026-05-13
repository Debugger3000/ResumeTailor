import os
from ollama import AsyncClient
from const.ai_models import ModelProvider

# ---
# Ollama info
# ---
# Model: (llama3.1:8b)
# secret key: dont need for local

# OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
# DEFAULT_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')


from typing import Optional


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

# # Single shared client instance — import this anywhere
# client = AsyncClient(host=OLLAMA_HOST)
# cur_model = None

# # Setup ollama global client for server environment...
# #
# async def set_ollama_client(model: ModelProvider):
#     model_name = model.get("model_name")
#     host = model.get("host")
#     client = AsyncClient(host)
#     this.cur_model = model_name
#     cur_model

# # ollama client functions 

# # Send a chat message list, return the assistant's text reply.
# async def chat(messages: list[dict], model: str = cur_model, **kwargs) -> str:
#     response = await client.chat(model=model, messages=messages, **kwargs)
#     return response['message']['content']


# async def chat_stream(messages: list[dict], model: str = DEFAULT_MODEL):
#     """Stream tokens as they arrive. Yields strings."""
#     async for chunk in await client.chat(
#         model=model, messages=messages, stream=True
#     ):
#         yield chunk['message']['content']


# async def generate(prompt: str, system: str | None = None, model: str = DEFAULT_MODEL) -> str:
#     """One-shot prompt without conversation history."""
#     response = await client.generate(model=model, prompt=prompt, system=system)
#     return response['response']


# async def embed(text: str, model: str = 'nomic-embed-text') -> list[float]:
#     """Get an embedding vector for text."""
#     response = await client.embeddings(model=model, prompt=text)
#     return response['embedding']