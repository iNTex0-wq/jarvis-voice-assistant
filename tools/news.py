"""News tool — Google News RSS, free, no API key."""
import xml.etree.ElementTree as ET

import requests

RSS_URL = "https://news.google.com/rss/search"


def get_news(topic: str, max_headlines: int = 5) -> dict:
    resp = requests.get(
        RSS_URL,
        params={"q": topic, "hl": "en-US", "gl": "US", "ceid": "US:en"},
        timeout=10,
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = root.findall(".//item")[:max_headlines]
    if not items:
        return {"error": f"No news found for '{topic}'"}

    headlines = [
        {
            "title": item.findtext("title", default="").strip(),
            "source": item.findtext("source", default="").strip(),
        }
        for item in items
    ]

    return {"topic": topic, "headlines": headlines}
