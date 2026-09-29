"""
Strips obvious personal identifiers (phone numbers, email addresses)
out of the text BEFORE it's sent to any LLM API. This protects the
sender's/victim's personal info from ending up in a third-party
provider's logs. It runs before every LLM call in the orchestrator.
"""
import re

EMAIL_RE = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")
PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}")


def redact(text):
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text
