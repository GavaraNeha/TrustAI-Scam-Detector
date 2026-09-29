"""
Tavily search wrapper. Free tier: 1,000 credits/month, no card
required. Each call below costs 1 credit regardless of max_results.
"""
import requests

import config


def search_web(query, max_results=5):
    """
    Returns a list of {title, url, content} dicts, or [] on any
    failure (missing key, network error, rate limit) so callers can
    treat "no evidence found" and "search failed" the same way:
    they both mean "can't verify from search".
    """
    if not config.TAVILY_API_KEY:
        return []

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=20,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
            for r in results
        ]
    except Exception:
        return []
