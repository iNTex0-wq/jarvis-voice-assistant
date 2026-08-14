"""Config for JARVIS. Loads from .env with sensible defaults."""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    # LLM backend
    LLM_BACKEND: str = os.getenv("LLM_BACKEND", "ollama")

    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # Web search (Tavily)
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Proxmox (M630e)
    PROXMOX_HOST: str = os.getenv("PROXMOX_HOST", "https://192.168.1.X:8006")
    PROXMOX_NODE: str = os.getenv("PROXMOX_NODE", "pve")
    PROXMOX_TOKEN_ID: str = os.getenv("PROXMOX_TOKEN_ID", "")
    PROXMOX_TOKEN_SECRET: str = os.getenv("PROXMOX_TOKEN_SECRET", "")
    PROXMOX_VERIFY_SSL: bool = os.getenv("PROXMOX_VERIFY_SSL", "false").lower() == "true"

    # Assistant identity
    ASSISTANT_NAME: str = os.getenv("ASSISTANT_NAME", "Jarvis")
    WAKE_WORD: str = os.getenv("WAKE_WORD", "jarvis")


config = Config()
