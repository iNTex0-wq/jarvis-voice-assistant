"""JARVIS Orchestrator — the core loop. Takes user input, sends it to the
LLM with available tools, executes any tool calls, feeds results back,
and returns a final answer. Backend-agnostic (Ollama or Claude)."""
import json

from config import config
from llm import get_llm
from tools.registry import TOOLS, execute_tool

SYSTEM_PROMPT = f"""You are {config.ASSISTANT_NAME}, a helpful voice assistant \
running on the user's homelab. You can check the status of their Proxmox \
server (an M630e) including containers, VMs, and resource usage.

Only use the Proxmox tools when the user is actually asking about their \
server, containers, VMs, or homelab status. Use the weather tool only \
when asked about weather or conditions somewhere. Use the news tool only \
when asked about current events, news, or headlines about a topic or \
place. If you don't know the answer to something yourself — a company, \
person, fact, or anything specific you're unsure about — use the \
search_web tool to look it up rather than saying you don't know. For \
general conversation, writing code, or math you can already do, answer \
directly and do NOT call any tool.

Keep responses concise and conversational — you'll be read aloud via \
text-to-speech, so avoid long lists, markdown, or special formatting. \
Speak naturally, like a helpful assistant, not a script. When summarizing \
news headlines, mention 2-3 of the most relevant ones conversationally \
rather than reading a full list.

When asked to write or generate code: write the full code in a fenced \
code block (```) as normal. Then, separately, give a short spoken \
walkthrough in plain conversational language — explain what the code \
does and call out the important variable and function names by name \
(e.g. "I created a function called calculate_total that takes price and \
quantity as inputs"). Do not try to read the code's symbols, brackets, \
or punctuation aloud — describe its purpose and structure in words \
instead. The fenced code block will be shown on screen; only your \
spoken walkthrough gets read aloud.
"""

# keeps requests fast even in a long conversation
MAX_HISTORY_MESSAGES = 16


class Orchestrator:
    def __init__(self):
        self.llm = get_llm()
        self.history: list[dict] = []

    def ask(self, user_input: str, max_tool_hops: int = 5) -> str:
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()

        for _ in range(max_tool_hops):
            response = self.llm.chat(
                messages=self.history,
                tools=TOOLS,
                system=SYSTEM_PROMPT,
            )

            if not response.tool_calls:
                text = response.text.strip()
                if not text:
                    print(f"[debug] empty response from model, raw: {response.raw}")
                    text = "Sorry, I'm not sure how to answer that one — could you rephrase?"
                self.history.append({"role": "assistant", "content": text})
                return text

            self.history.append({"role": "assistant", "content": response.text or ""})

            for call in response.tool_calls:
                result = execute_tool(call.name, call.arguments)
                print(f"[debug] tool called: {call.name}({call.arguments}) -> {result}")
                self.history.append(
                    {
                        "role": "tool",
                        "content": json.dumps(result),
                        "name": call.name,
                    }
                )

        return "Sorry, I got stuck trying to look that up."

    def _trim_history(self):
        if len(self.history) > MAX_HISTORY_MESSAGES:
            self.history = self.history[-MAX_HISTORY_MESSAGES:]

    def reset(self):
        self.history = []


if __name__ == "__main__":
    print(f"{config.ASSISTANT_NAME} online (backend: {config.LLM_BACKEND}). Type 'quit' to exit.\n")
    orch = Orchestrator()
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        answer = orch.ask(user_input)
        print(f"{config.ASSISTANT_NAME}: {answer}\n")
