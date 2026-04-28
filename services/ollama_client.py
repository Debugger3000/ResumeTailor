import os
from ollama import AsyncClient


# ---
# Ollama info
# ---
# Model: (llama3.1:8b)
# secret key: dont need for local

OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
DEFAULT_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')



# Single shared client instance — import this anywhere
client = AsyncClient(host=OLLAMA_HOST)


async def chat(messages: list[dict], model: str = DEFAULT_MODEL, **kwargs) -> str:
    """Send a chat message list, return the assistant's text reply."""
    response = await client.chat(model=model, messages=messages, **kwargs)
    return response['message']['content']


async def chat_stream(messages: list[dict], model: str = DEFAULT_MODEL):
    """Stream tokens as they arrive. Yields strings."""
    async for chunk in await client.chat(
        model=model, messages=messages, stream=True
    ):
        yield chunk['message']['content']


async def generate(prompt: str, system: str | None = None, model: str = DEFAULT_MODEL) -> str:
    """One-shot prompt without conversation history."""
    response = await client.generate(model=model, prompt=prompt, system=system)
    return response['response']


async def embed(text: str, model: str = 'nomic-embed-text') -> list[float]:
    """Get an embedding vector for text."""
    response = await client.embeddings(model=model, prompt=text)
    return response['embedding']