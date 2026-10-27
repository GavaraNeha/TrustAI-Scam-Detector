"""
Looks up a company via Tavily search.

Scam reports only count if they are about FAKE JOB/RECRUITMENT offers
using this company's name, and are NOT on the company's own website.
The company's own fraud-alert pages are recorded separately: they show
impersonation happens, not that the company is a scam.
"""
from services.search import search_web
from services import cache
from pipeline.domain_utils import registered_domain, domain_label, company_slugs

SCAM_KEYWORDS = ["scam", "fraud", "fake", "beware", "duped", "cheated"]
RECRUIT_WORDS = [
    "recruit", "job offer", "job scam", "hiring", "internship",
    "interview", "offer letter", "placement", "employment", "career",
]


def _empty():
    return {
        "evidence": [],
        "scam_reports_found": False,
        "official_presence_found": False,
        "official_domains": [],
        "official_fraud_alert": False,
    }


def research_company(company_name):
    if not company_name:
        return _empty()

    cached = cache.get("company_v2", company_name)
    if cached:
        return cached

    slugs = company_slugs(company_name)
    name_l = company_name.lower()

    def is_own(r):
        return domain_label(registered_domain(r["url"])) in slugs

    report_results = search_web(f'"{company_name}" fake job offer recruitment scam')
    reports = []
    fraud_alert = False
    for r in report_results:
        text = f'{r["title"]} {r["content"]}'.lower()
        if name_l not in text:
            continue
        if not any(k in text for k in SCAM_KEYWORDS):
            continue
        if not any(k in text for k in RECRUIT_WORDS):
            continue
        if is_own(r):
            fraud_alert = True
            continue
        reports.append(r)

    official_results = search_web(f"{company_name} official careers website")
    own_pages = [r for r in official_results if is_own(r)]

    official_domains = sorted({
        registered_domain(r["url"])
        for r in official_results + report_results
        if is_own(r)
    })

    evidence, seen = [], set()
    for r in reports[:2] + own_pages[:2]:
        if r["url"] not in seen:
            seen.add(r["url"])
            evidence.append({"title": r["title"], "url": r["url"]})

    result = {
        "evidence": evidence,
        "scam_reports_found": len(reports) > 0,
        "official_presence_found": len(own_pages) > 0,
        "official_domains": official_domains,
        "official_fraud_alert": fraud_alert,
    }

    cache.set("company_v2", company_name, result)
    return result
