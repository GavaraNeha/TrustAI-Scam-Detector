"""
Prepares "resume value" context for the synthesizer. This does NOT
make the final worth-it call itself -- it packages cheap, rule-based
observations (unpaid, vague role, no real company evidence) that the
synthesizer's LLM call reasons over alongside the search evidence.
Keeping this separate from safety_rules.py because "is this a scam"
and "is this worth your time" are different questions, even for a
totally legitimate, non-scammy but low-value opportunity.
"""

def build_value_context(extracted, company_research):
    notes = []

    stipend = (extracted.get("stipend_or_pay") or "").lower()
    if not stipend or "unpaid" in stipend or stipend in ("none", "n/a"):
        notes.append("No stated pay/stipend — evaluate purely on learning/resume value.")

    if not extracted.get("role_title"):
        notes.append("No specific role title given — vague role descriptions are a low-value signal.")

    if not company_research.get("official_presence_found"):
        notes.append("No official company web/careers presence found in search — can't confirm this is a real organization.")

    if company_research.get("scam_reports_found"):
        notes.append("Search found scam/fraud reports mentioning this company.")

    perks = extracted.get("claimed_perks") or []
    if any("certificate" in p.lower() for p in perks) and not stipend:
        notes.append("Unpaid role advertising mainly a certificate — check if it involves real deliverables, not just a certificate mill.")

    return notes
