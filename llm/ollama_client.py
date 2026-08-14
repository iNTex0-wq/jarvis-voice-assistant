"""Ollama backend."""
import requests

from config import config
from llm.base import LLMBackend, LLMResponse, ToolCall


class OllamaBackend(LLMBackend):
    def __init__(self, host: str | None = None, model: str | None = None):
        self.host = (host or config.OLLAMA_HOST).rstrip("/")
        self.model = model or config.OLLAMA_MODEL

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "think": False,  # qwen3 thinking mode can eat the whole token budget
            "options": {
                "num_predict": 500,
            },
        }
        if tools:
            payload["tools"] = tools

        resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        message = data.get("message", {})
        text = message.get("content", "") or ""

        tool_calls = []
        for i, tc in enumerate(message.get("tool_calls", []) or []):
            fn = tc.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=str(i),
                    name=fn.get("name", ""),
                    arguments=fn.get("arguments", {}) or {},
                )
            )

        return LLMResponse(text=text, tool_calls=tool_calls, raw=data)
