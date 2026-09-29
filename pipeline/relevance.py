"""
Gate stage: is this even an opportunity/job/internship message?
Runs before any of the expensive checks (search, URL intel), so a
cab-booking diagram or a random paragraph doesn't get scored at all
-- it gets told plainly that it isn't an opportunity message.
"""
from services.llm import chat_json

SYSTEM_PROMPT = """You classify whether a piece of text is a job offer, internship
offer, or similar "opportunity" message (the kind a student might receive by
email, SMS, or WhatsApp). Diagrams, unrelated documents, personal messages,
and general text are NOT opportunity messages.

Return JSON: {"is_opportunity": true or false, "reason": "one short sentence"}"""


def check_relevance(text):
    result = chat_json(SYSTEM_PROMPT, text[:4000])

    if result is None:
        # LLM unavailable -- don't block the pipeline, just proceed
        # without the gate and let downstream stages do their best.
        return {"is_opportunity": True, "reason": "Relevance check unavailable, proceeding anyway."}

    return {
        "is_opportunity": bool(result.get("is_opportunity", True)),
        "reason": result.get("reason", ""),
    }
