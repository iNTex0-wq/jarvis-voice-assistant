"""Backend factory — the one place that decides Ollama vs Claude."""
from config import config
from llm.base import LLMBackend


def get_llm() -> LLMBackend:
    if config.LLM_BACKEND == "ollama":
        from llm.ollama_client import OllamaBackend
        return OllamaBackend()
    elif config.LLM_BACKEND == "claude":
        from llm.claude_client import ClaudeBackend
        return ClaudeBackend()
    else:
        raise ValueError(f"Unknown LLM_BACKEND: {config.LLM_BACKEND}")
