"""
Final stage: combines everything gathered so far (extracted fields,
rule-based safety score, URL intel, company search evidence, value
notes) and asks the LLM to produce the two verdicts, reasoning ONLY
over the evidence provided -- never inventing facts about the
company that weren't found.
"""
import json
from services.llm import chat_json

SYSTEM_PROMPT = """You are judging a job/internship opportunity message for two things:

1. SAFETY: is this likely a scam? Base this on the rule-based flags and URL/company
   evidence given to you -- do not invent additional reasons.
2. WORTH IT: even if not a scam, is this a good use of a student's time / does it add
   real resume value? Consider pay, role clarity, company legitimacy, and the value
   notes given.

If the evidence given is too thin to be confident (e.g. no search results found,
company name unknown), say so honestly rather than guessing -- use "Can't verify"
verdicts rather than fabricating certainty.

Return JSON exactly in this shape:
{
  "safety_verdict": "Safe" | "Suspicious" | "Scam Likely" | "Can't Verify",
  "safety_score": 0-100,
  "worth_verdict": "Strong" | "Decent" | "Weak" | "Can't Tell",
  "worth_score": 0-100,
  "reasons": [string, ...],
  "questions_to_ask": [string, ...]
}"""


def synthesize(extracted, rule_score, rule_reasons, url_intel_results, company_research, value_notes):
    context = {
        "extracted_fields": extracted,
        "rule_based_score": rule_score,
        "rule_based_reasons": rule_reasons,
        "url_intel": url_intel_results,
        "company_research": company_research,
        "value_notes": value_notes,
    }

    result = chat_json(SYSTEM_PROMPT, json.dumps(context, default=str))

    if result is None:
        # LLM unavailable -- fall back to a purely rule-based verdict
        # rather than failing the whole request.
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
            "reasons": rule_reasons + value_notes,
            "questions_to_ask": [],
            "_llm_unavailable": True,
        }

    result.setdefault("reasons", [])
    result.setdefault("questions_to_ask", [])
    result["_llm_unavailable"] = False
    return result
