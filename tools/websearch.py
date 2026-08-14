"""Web search tool — Tavily API. Free tier: 1,000 searches/month.
Returns a synthesized answer plus a few sources, good for TTS."""
import requests

from config import config

TAVILY_URL = "https://api.tavily.com/search"


def search_web(query: str) -> dict:
    if not config.TAVILY_API_KEY:
        return {"error": "Web search isn't configured — no TAVILY_API_KEY set in .env"}

    resp = requests.post(
        TAVILY_URL,
        json={
            "api_key": config.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 3,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    sources = [
        {"title": r.get("title", ""), "snippet": r.get("content", "")[:200]}
        for r in data.get("results", [])[:3]
    ]

    return {"query": query, "answer": data.get("answer", ""), "sources": sources}
