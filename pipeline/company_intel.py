"""
Looks up a company via Tavily search: do people call it a scam, does
it have an ordinary official web/careers presence. Cached so the
same company isn't re-searched (and re-billed) every time it appears.
"""
from services.search import search_web
from services import cache

SCAM_KEYWORDS = ["scam", "fraud", "fake", "cheated", "beware", "duped"]


def research_company(company_name):
    if not company_name:
        return {"evidence": [], "scam_reports_found": False, "official_presence_found": False}

    cached = cache.get("company", company_name)
    if cached:
        return cached

    evidence = []

    scam_results = search_web(f'"{company_name}" scam reviews')
    flagged = [
        r for r in scam_results
        if any(k in (r["title"] + r["content"]).lower() for k in SCAM_KEYWORDS)
    ]
    evidence.extend(flagged[:2])

    official_results = search_web(f"{company_name} official website careers")
    evidence.extend(official_results[:2])

    result = {
        "evidence": [{"title": e["title"], "url": e["url"]} for e in evidence],
        "scam_reports_found": len(flagged) > 0,
        "official_presence_found": len(official_results) > 0,
    }

    cache.set("company", company_name, result)
    return result
