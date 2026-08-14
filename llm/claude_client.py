"""Claude API backend. Not used by default — set LLM_BACKEND=claude
and ANTHROPIC_API_KEY in .env to switch. Requires: pip install anthropic"""
from config import config
from llm.base import LLMBackend, LLMResponse, ToolCall


class ClaudeBackend(LLMBackend):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key or config.ANTHROPIC_API_KEY)
        self.model = model or config.CLAUDE_MODEL

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        claude_tools = None
        if tools:
            claude_tools = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system or "",
            messages=messages,
            tools=claude_tools or [],
        )

        text = ""
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=block.input)
                )

        return LLMResponse(text=text, tool_calls=tool_calls, raw=resp)
