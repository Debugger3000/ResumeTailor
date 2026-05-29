# ai/clients/gemini_client.py
import json
from google import genai
from google.genai import types



def _to_gemini_schema(node: dict) -> types.Schema:
    type_map = {
        "object": types.Type.OBJECT,
        "array": types.Type.ARRAY,
        "string": types.Type.STRING,
        "integer": types.Type.INTEGER,
        "number": types.Type.NUMBER,
        "boolean": types.Type.BOOLEAN,
    }
    t = node["type"]
    kwargs = {"type": type_map[t]}

    if t == "object":
        kwargs["properties"] = {
            k: _to_gemini_schema(v) for k, v in node.get("properties", {}).items()
        }
        if "required" in node:
            kwargs["required"] = node["required"]
    elif t == "array":
        kwargs["items"] = _to_gemini_schema(node["items"])

    if "enum" in node:
        kwargs["enum"] = node["enum"]
    if "description" in node:
        kwargs["description"] = node["description"]

    return types.Schema(**kwargs)

class GeminiClient:
    def __init__(self):
        self._client: genai.Client | None = None
        self.model: str | None = None

    def configure(self, model: dict) -> None:
        self.model = model.get("model_name")
        api_key = model.get("api_key_env")
        if not api_key:
            raise RuntimeError("No Gemini API key set (GEMINI_API_KEY)")
        if not self.model:
            raise RuntimeError("model_config.model_name is not set")
        self._client = genai.Client(api_key=api_key)

    async def chat(self, messages, schema=None, temperature=0.0, max_tokens=4096):
        if self._client is None:
            raise RuntimeError("Gemini client not configured")

        # Gemini takes the system prompt in config.system_instruction (like Claude's
        # top-level `system`), NOT as a message. It also uses the role "model"
        # instead of "assistant".
        system = None
        contents = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                role = "model" if m["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})

        config_kwargs = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system:
            config_kwargs["system_instruction"] = system

        # Structured output (your Ollama `format=SCHEMA` equivalent).
        # Note: Gemini's response_schema is an OpenAPI subset, not full JSON Schema.
        if schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            # convert my schema to schema that gemini needs
            config_kwargs["response_schema"] = _to_gemini_schema(schema)

        resp = await self._client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        if schema is not None:
            # response.text is a JSON string matching the schema
            return json.loads(resp.text)  # dict already matching schema

        return resp.text


gemini_client = GeminiClient()