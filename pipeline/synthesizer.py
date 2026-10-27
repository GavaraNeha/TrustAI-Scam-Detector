"""
Final stage: combines everything gathered so far and asks the LLM for
the two verdicts, reasoning ONLY over the evidence provided. Deterministic
guardrails then stop the LLM from contradicting hard evidence.

safety_score = scam likelihood (0 = clearly legitimate, 100 = certain scam).
"""
import json
import re
from services.llm import chat_json

MAX_QUESTIONS = 5

SYSTEM_PROMPT = """You are judging a job/internship opportunity message for two things:

1. SAFETY: is THIS MESSAGE likely a scam? Base this ONLY on the rule-based flags, URL
   evidence, trust signals and company research given to you. Do not invent reasons.
   safety_score is the scam likelihood: 0 = clearly legitimate, 100 = certain scam.
2. WORTH IT: even if not a scam, is it a good use of a student's time / real resume value?
   Consider pay, role clarity, company legitimacy and the value notes.

Evidence rules (important):
- company_research.scam_reports_found = true means scammers are known to impersonate this
  company in fake offers. Every large company has this. It is NOT evidence that this
  message is a scam and NOT a red flag about the company. Never list it as a red flag
  unless the message itself shows red flags (rule flags, bad link domain, free-mail
  recruiter, fee request). If the message looks clean, it may at most appear as a
  question: "verify through the official careers site".
- company_research.official_fraud_alert = true is the company's own impersonation
  warning. Not evidence against the company.
- VirusTotal "queued", "skipped" or "error" and WHOIS failures or missing data are
  NEUTRAL. Never list them as red flags.
- trust_signals.official_link_domain or official_sender_domain = true is a strong
  legitimacy signal.
- Missing stipend, role title, sender or contact details is NOT a scam indicator by
  itself. Mention it only in worth_it reasoning or in questions_to_ask, never in red_flags.
- Do not mention numeric rule scores.
- Put only genuine concerns in red_flags and only genuine positives in green_flags.
  Never put the same point in both. Each item: one sentence, under 25 words.
- questions_to_ask: at most 5, most important first.

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

# Red flags that only say "we couldn't check" are neutral, drop them.
_NEUTRAL_RE = re.compile(
    r"(whois|virustotal|domain registration|lookup|first-time url|queued)"
    r".*(fail|unknown|unavailable|not available|no data|no result|unable|queued|not analy|skipped|error)"
    r"|(fail|unknown|unable|not available).*(whois|virustotal|lookup)",
    re.IGNORECASE,
)

# "Missing detail" flags (no stipend, sender not given...). Not scam signals:
# they are dropped from red flags unless there is hard rule-based evidence.
_MISSING_RE = re.compile(
    r"\b(no|missing|not provided|not given|not listed|unverified|absent|lacks?|without)\b"
    r".*\b(stipend|pay|salary|sender|contact|e-?mail domain|role title|job title|details|channel|description)\b"
    r"|\b(stipend|pay|salary|sender|contact|e-?mail domain|role title|job title|details)\b"
    r".*\b(missing|not provided|not given|not listed|unverified|absent|unknown|is vague)\b",
    re.IGNORECASE,
)


def _dedupe(items):
    seen, out = set(), []
    for i in items:
        key = i.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(i)
    return out


def _clean_red_flags(red, rule_score):
    red = [r for r in red if not _NEUTRAL_RE.search(r)]
    if rule_score < 30:
        red = [r for r in red if not _MISSING_RE.search(r)]
    return red


def _guardrails(result, rule_score, trust):
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
    ):
        # Clean message on the company's own domain: impersonation articles
        # about the company don't change that.
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
        red = result.get("reasons", [])
    green = result.pop("green_flags", [])

    result = _guardrails(result, rule_score, trust)

    result["reasons"] = _dedupe(_clean_red_flags(red, rule_score))  # UI shows `reasons` as red flags
    result["green_flags"] = _dedupe(list(green) + green_hints)
    result["questions_to_ask"] = (result.get("questions_to_ask") or [])[:MAX_QUESTIONS]
    result["_llm_unavailable"] = False
    return result
