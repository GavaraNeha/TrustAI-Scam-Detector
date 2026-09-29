"""
Template-based verification reply -- deliberately NOT an LLM call,
so it always works even if both Groq and Gemini are down or rate
limited, and it can't accidentally invent claims about the company.
"""

def generate_reply(extracted, safety_verdict):
    if safety_verdict == "Safe":
        return None

    company = extracted.get("company_name") or "your company"

    lines = [
        f"Hi, thank you for reaching out about this opportunity at {company}.",
        "Before I proceed, could you please share a few details to help me verify the role:",
        "",
        f"1. Could you send this offer from an official {company} email domain "
        f"(not a personal Gmail/Yahoo address)?",
        "2. Could you share the company's GST number or CIN (for Indian companies)?",
        "3. Is there a listing for this role on the company's official careers page or LinkedIn?",
        "4. Would it be possible to have a short verification call on the company's official number?",
        "",
        "Happy to move forward once I can confirm these — thank you for understanding.",
    ]

    return "\n".join(lines)
