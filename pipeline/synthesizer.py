"""
Final stage: combines everything gathered so far and asks the LLM for
the two verdicts, reasoning ONLY over the evidence provided. A few
deterministic guardrails then stop the LLM from contradicting hard evidence.

safety_score = scam likelihood (0 = clearly legitimate, 100 = certain scam).
"""
import json
from services.llm import chat_json

SYSTEM_PROMPT = """You are judging a job/internship opportunity message for two things:

1. SAFETY: is this likely a scam? Base this ONLY on the rule-based flags, URL evidence,
   trust signals and company research given to you. Do not invent reasons.
   safety_score is the scam likelihood: 0 = clearly legitimate, 100 = certain scam.
2. WORTH IT: even if not a scam, is it a good use of a student's time / real resume value?
   Consider pay, role clarity, company legitimacy and the value notes.

Evidence rules (important):
- company_research.scam_reports_found is true ONLY if search found reports of fake
  job/recruitment offers using this company's name. If false, never claim scam
  reports exist for the company.
- company_research.official_fraud_alert = true means the company itself publishes a
  warning about recruitment impersonation. That is NOT evidence against the company.
  At most, advise using official channels only.
- VirusTotal "queued", "skipped" or "error" and WHOIS failures are NEUTRAL. Never list
  them as red flags and never treat "no data" as suspicious.
- trust_signals.official_link_domain or official_sender_domain = true is a strong
  legitimacy signal.
- Do not mention numeric rule scores in your reasons.
- Put only genuine concerns in red_flags and only genuine positives in green_flags.
  Never put the same point in both.
- Each item: one sentence, under 25 words.

If evidence is too thin to be confident, use "Can't Verify" / "Can't Tell" instead of guessing.

Return JSON exactly in this shape:
{
  "safety_verdict": "Safe" | "Suspicious" | "Scam Likely" | "Can't Verify",
  "safety_score": 0-100,
  "worth_verdict": "Strong" | "Decent" | "Weak" | "Can't Tell",
  "worth_score": 0-100,
  "red_flags": [string, ...],
  "green_flags": [string, ...],
  "questions_to_ask": [string, ...]
}"""


def _dedupe(items):
    seen, out = set(), []
    for i in items:
        key = i.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(i)
    return out


def _guardrails(result, rule_score, trust, company_research):
    verdict = result.get("safety_verdict")
    score = result.get("safety_score") or 0

    if rule_score >= 60 and verdict != "Scam Likely":
        result["safety_verdict"] = "Scam Likely"
        result["safety_score"] = max(score, 80)
    elif rule_score >= 30 and verdict in ("Safe", "Can't Verify"):
        result["safety_verdict"] = "Suspicious"
        result["safety_score"] = max(score, 50)
    elif (
        rule_score == 0
        and (trust.get("official_link_domain") or trust.get("official_sender_domain"))
        and not trust.get("url_flags")
        and not company_research.get("scam_reports_found")
    ):
        result["safety_verdict"] = "Safe"
        result["safety_score"] = min(score, 15)

    return result


def synthesize(extracted, rule_score, rule_reasons, url_intel_results,
               company_research, value_notes, trust=None, green_hints=None):
    trust = trust or {}
    green_hints = green_hints or []

    context = {
        "extracted_fields": extracted,
        "rule_based_score": rule_score,
        "rule_based_reasons": rule_reasons,
        "url_intel": url_intel_results,
        "company_research": company_research,
        "trust_signals": trust,
        "value_notes": value_notes,
    }

    result = chat_json(SYSTEM_PROMPT, json.dumps(context, default=str))

    if result is None:
        if rule_score >= 60:
            safety_verdict = "Scam Likely"
        elif rule_score >= 30:
            safety_verdict = "Suspicious"
        else:
            safety_verdict = "Safe"

        return {
            "safety_verdict": safety_verdict,
            "safety_score": min(rule_score, 100),
            "worth_verdict": "Can't Tell",
            "worth_score": 0,
            "reasons": rule_reasons,
            "green_flags": _dedupe(green_hints),
            "questions_to_ask": [],
            "_llm_unavailable": True,
        }

    red = result.pop("red_flags", None)
    if red is None:
        red = result.get("reasons", [])  # tolerate old-shape output
    green = result.pop("green_flags", [])

    result = _guardrails(result, rule_score, trust, company_research)

    result["reasons"] = _dedupe(red)  # template shows `reasons` as red flags
    result["green_flags"] = _dedupe(list(green) + green_hints)
    result.setdefault("questions_to_ask", [])
    result["_llm_unavailable"] = False
    return result
