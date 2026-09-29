"""
Runs every stage in order and assembles the final result dict the
template renders. This is the one function app.py calls.

Order matters: relevance gate first (cheapest, avoids wasting search/
LLM quota on irrelevant text), then extraction, then the checks that
need the extracted fields (URL intel, company research), then the
synthesizer that reasons over everything gathered.
"""
from pipeline.ingest import build_text, extract_urls
from pipeline.redact import redact
from pipeline.relevance import check_relevance
from pipeline.extractor import extract_fields
from pipeline.safety_rules import check_text_rules, check_sender_domain
from pipeline.url_intel import check_url
from pipeline.company_intel import research_company
from pipeline.value_scorer import build_value_context
from pipeline.synthesizer import synthesize
from pipeline.reply_generator import generate_reply


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

    rule_score, rule_reasons = check_text_rules(clean_text, category=category)
    domain_risk, domain_reasons = check_sender_domain(
        extracted.get("sender_email_domain"), extracted.get("company_name")
    )
    rule_score += domain_risk
    rule_reasons += domain_reasons

    urls = extracted.get("links_mentioned") or extract_urls(clean_text)
    url_intel_results = [check_url(u) for u in urls[:3]]  # cap at 3 to protect free-tier quota

    company_research = research_company(extracted.get("company_name"))
    value_notes = build_value_context(extracted, company_research)

    synthesis = synthesize(
        extracted, rule_score, rule_reasons, url_intel_results, company_research, value_notes
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
        "questions_to_ask": synthesis["questions_to_ask"],
        "evidence": company_research.get("evidence", []),
        "url_intel": url_intel_results,
        "suggested_reply": reply,
        "llm_unavailable": synthesis.get("_llm_unavailable", False),
    }
