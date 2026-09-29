"""
Pulls structured fields out of the raw message text using the LLM.
This replaces guessing a company name with regex -- the LLM reads
the whole message and returns what it can confidently find.
"""
from services.llm import chat_json

SYSTEM_PROMPT = """You extract structured facts from a job/internship offer message.
Only report what is actually stated in the text -- use null for anything not mentioned.
Do not guess or invent values.

Return JSON with exactly these fields:
{
  "company_name": string or null,
  "role_title": string or null,
  "opportunity_type": "internship" | "job" | "freelance" | "other" | null,
  "stipend_or_pay": string or null (quote it as written, e.g. "$45/hr", "unpaid"),
  "asks_for_fee": true or false,
  "fee_details": string or null,
  "contact_channel": "email" | "whatsapp" | "telegram" | "phone" | "other" | null,
  "sender_email_domain": string or null,
  "links_mentioned": [string, ...],
  "claimed_perks": [string, ...]
}"""


def extract_fields(text):
    result = chat_json(SYSTEM_PROMPT, text[:6000])

    if result is None:
        return {
            "company_name": None,
            "role_title": None,
            "opportunity_type": None,
            "stipend_or_pay": None,
            "asks_for_fee": False,
            "fee_details": None,
            "contact_channel": None,
            "sender_email_domain": None,
            "links_mentioned": [],
            "claimed_perks": [],
            "_extraction_failed": True,
        }

    result.setdefault("links_mentioned", [])
    result.setdefault("claimed_perks", [])
    result["_extraction_failed"] = False
    return result
