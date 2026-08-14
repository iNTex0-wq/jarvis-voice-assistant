"""Tool schemas + name-to-function map for the LLM to call."""
from tools import news
from tools import proxmox
from tools import weather
from tools import websearch

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_node_status",
            "description": "Get CPU, memory, and uptime stats for the homelab server (M630e).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_containers",
            "description": "List all LXC containers on the homelab server and whether they're running or stopped.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_vms",
            "description": "List all virtual machines on the homelab server and their status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_container_status",
            "description": "Check the status of a specific container by name (e.g. 'jellyfin', 'pihole') or its VMID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_or_vmid": {
                        "type": "string",
                        "description": "The container name or VMID to check.",
                    }
                },
                "required": ["name_or_vmid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather (temperature, conditions, wind) for any city or location by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and optionally country/state, e.g. 'Boston' or 'Tirana, Albania'.",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "Get current news headlines about a topic, country, or subject.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "What to get news about, e.g. 'Albania', 'technology', 'stock market'.",
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for general facts, companies, people, or anything not covered by the other tools. Use this when you don't know the answer yourself and it's not a Proxmox, weather, or news question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "get_node_status": proxmox.get_node_status,
    "list_containers": proxmox.list_containers,
    "list_vms": proxmox.list_vms,
    "get_container_status": proxmox.get_container_status,
    "get_weather": weather.get_weather,
    "get_news": news.get_news,
    "search_web": websearch.search_web,
}


def execute_tool(name: str, arguments: dict):
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**arguments)
    except Exception as e:
        return {"error": str(e)}
