
from enum import Enum
from typing import TypedDict


class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"

class OllamaStatus(TypedDict):
    running: bool
    provider: str
    host: str
    model_name: str
    loaded_models: list[str]
    error: str | None


class ModelType(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"

