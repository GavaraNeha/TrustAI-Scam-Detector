"""
Runs every stage in order and assembles the final result dict the
template renders. This is the one function app.py calls.

Order: relevance gate -> extraction -> text rules -> company research
(needed to know the official domains) -> URL checks -> synthesizer.
"""
import re

from pipeline.ingest import build_text, extract_urls
from pipeline.redact import redact
from pipeline.relevance import check_relevance
from pipeline.extractor import extract_fields
from pipeline.safety_rules import (
    check_text_rules, check_sender_domain, check_emails_in_text, FREEMAIL_DOMAINS,
)
from pipeline.url_intel import check_url
from pipeline.company_intel import research_company
from pipeline.value_scorer import build_value_context
from pipeline.synthesizer import synthesize
from pipeline.reply_generator import generate_reply
from pipeline.domain_utils import registered_domain, domain_label, company_slugs

# Email addresses are removed BEFORE link scanning, otherwise
# "wipro.hiring2026@gmail.com" is misread as the link "wipro.hiring".
_EMAIL_STRIP_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# Bare domains like careers.microsoft.com/apply. The (?![\w@-]) after the TLD
# stops a match from ending in the middle of a word.
_LINK_RE = re.compile(
    r"(?<![@\w.-])(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?![\w@-])(?:/[^\s,;)\]]*)?",
    re.IGNORECASE,
)
_NOT_LINKS = {"e.g", "i.e"}


def _find_links(text):
    flat = _EMAIL_STRIP_RE.sub(" ", " ".join((text or "").split()))
    out = []
    for m in _LINK_RE.finditer(flat):
        link = m.group(0).rstrip(".")
        host = link.split("//")[-1].split("/")[0].lower()
        if host in FREEMAIL_DOMAINS or host in _NOT_LINKS or "." not in host:
            continue
        out.append(link)
    return out


def _collect_urls(extracted, clean_text, raw_text):
    urls = list(extracted.get("links_mentioned") or [])
    try:
        urls += list(extract_urls(clean_text) or [])
    except Exception:
        pass
    urls += _find_links(raw_text)

    seen, out = set(), []
    for u in urls:
        # drop anything that is really part of an email address
        if "@" in u:
            continue
        key = registered_domain(u) or u.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(u)
    return out


def _assess_urls(results, official_domains, company_name):
    """Deterministic URL risk. Returns (risk, red_flags, green_flags, official_hit).
    Unknown data (WHOIS failed, VirusTotal queued) is neutral, never a red flag."""
    risk, red, green = 0, [], []
    official_hit = False
    slugs = company_slugs(company_name)

    for r in results:
        dom = registered_domain(r["url"])
        label = domain_label(dom)
        age = (r.get("domain_age") or {}).get("age_days")
        stats = (r.get("virustotal") or {}).get("stats") or {}
        detections = (stats.get("malicious", 0) or 0) + (stats.get("suspicious", 0) or 0)

        is_official = dom in official_domains or (
            label in slugs and (
                (age is not None and age >= 730)
                or (age is None and dom.endswith(".com"))  # exact name + .com, no WHOIS data
            )
        )

        if is_official:
            official_hit = True
            green.append(f"Link points to {dom}, which matches the company's official website")
            continue

        if slugs and any(s in label for s in slugs):
            risk += 60
            red.append(f"Link domain {dom} imitates the company name but is not its official site")

        if age is not None and age < 180:
            risk += 30
            red.append(f"Link domain {dom} was registered only {age} days ago")

        if detections > 0:
            risk += 40
            red.append(f"VirusTotal engines flagged {dom} ({detections} detections)")

    return risk, red, green, official_hit


def run(message, screenshot_file, category=None):
    raw_text = build_text(message, screenshot_file)

    if not raw_text:
        return {"error": "No text or screenshot provided."}

    clean_text = redact(raw_text)

    relevance = check_relevance(clean_text)
    if not relevance["is_opportunity"]:
        return {
            "is_opportunity": False,
            "relevance_reason": relevance["reason"],
        }

    extracted = extract_fields(clean_text)
    company_name = extracted.get("company_name")

    rule_score, rule_reasons = check_text_rules(clean_text, category=category)

    domain_risk, domain_reasons = check_sender_domain(
        extracted.get("sender_email_domain"), company_name
    )
    if domain_risk == 0:
        domain_risk, domain_reasons = check_emails_in_text(raw_text, company_name)
    rule_score += domain_risk
    rule_reasons += domain_reasons

    company_research = research_company(company_name)
    official_domains = set(company_research.get("official_domains", []))

    urls = _collect_urls(extracted, clean_text, raw_text)
    url_intel_results = [
        check_url(u, official=registered_domain(u) in official_domains)
        for u in urls[:3]  # cap at 3 to protect free-tier quota
    ]

    url_risk, url_red, url_green, official_link = _assess_urls(
        url_intel_results, official_domains, company_name
    )
    rule_score += url_risk
    rule_reasons += url_red

    sender_domain = extracted.get("sender_email_domain")
    official_sender = bool(sender_domain) and registered_domain(sender_domain) in official_domains
    green_hints = list(url_green)
    if official_sender:
        green_hints.append(f"Sender email is on the company's official domain ({sender_domain})")

    trust = {
        "official_link_domain": official_link,
        "official_sender_domain": official_sender,
        "url_flags": bool(url_red),
    }

    value_notes = build_value_context(extracted, company_research)

    synthesis = synthesize(
        extracted, rule_score, rule_reasons, url_intel_results,
        company_research, value_notes, trust=trust, green_hints=green_hints,
    )

    reply = generate_reply(extracted, synthesis["safety_verdict"])

    return {
        "is_opportunity": True,
        "extracted": extracted,
        "safety_verdict": synthesis["safety_verdict"],
        "safety_score": synthesis["safety_score"],
        "worth_verdict": synthesis["worth_verdict"],
        "worth_score": synthesis["worth_score"],
        "reasons": synthesis["reasons"],
        "green_flags": synthesis.get("green_flags", []),
        "questions_to_ask": synthesis["questions_to_ask"],
        "evidence": company_research.get("evidence", []),
        "url_intel": url_intel_results,
        "suggested_reply": reply,
        "llm_unavailable": synthesis.get("_llm_unavailable", False),
    }
