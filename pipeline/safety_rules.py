"""
Plain-code, no-LLM-needed safety rules. Runs on the raw text.

Word-boundary fixed: earlier versions matched "pay" as a substring,
which flagged "Payment Gateway" in an unrelated diagram. Every rule
here uses \\b so it only matches whole words/phrases.
"""
import re

FREEMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "rediffmail.com", "live.com", "icloud.com", "protonmail.com",
}

CATEGORY_KEYWORDS = {
    "sms": [
        (r"\botp\b", 20, "Asks for an OTP over message — banks and real companies never do this"),
        (r"\bkyc\b", 20, "\"KYC\" scam pattern — a common banking-impersonation SMS scam"),
        (r"\baccount blocked\b", 20, "\"Account blocked\" urgency — a classic SMS phishing hook"),
        (r"\baccount suspended\b", 20, "\"Account suspended\" urgency — a classic SMS phishing hook"),
        (r"\bverify now\b", 15, "Pressures an immediate \"verify now\" action, a phishing pattern"),
    ],
    "email": [
        (r"\bverify your account\b", 20, "\"Verify your account\" — a common phishing pattern"),
        (r"\bsuspended\b", 15, "\"Account suspended\" urgency — a phishing pattern"),
        (r"\bupdate your payment\b", 20, "Asks to update payment details — common phishing bait"),
        (r"\bupdate your billing\b", 20, "Asks to update billing details — common phishing bait"),
        (r"\bclick below\b", 10, "\"Click below\" call-to-action — a phishing pattern"),
    ],
    "company": [],
    "internship": [],
}


def _wb(pattern):
    return re.compile(pattern, re.IGNORECASE)


BASE_RULES = [
    (_wb(r"\bfee\b|\bregistration fee\b"), 40, "Asks for money"),
    (_wb(r"\burgent\b|\blimited time\b|\blimited seats\b"), 20, "Creates urgency"),
    (_wb(r"\bwhatsapp\b|\btelegram\b"), 20, "Uses unofficial communication"),
    (_wb(r"\beasy money\b|\bno experience\b"), 20, "Too good to be true"),
    (_wb(r"\bno interview\b|\byou'?ve been selected\b"), 20, "Unrealistic hiring process"),
    (_wb(r"\bwork from home\b"), 10, "Generic job phrase"),
    (_wb(r"\bclick here\b|\bapply now\b"), 10, "Suspicious link language"),
    (_wb(r"\bguaranteed\b"), 10, "Unrealistic promises"),
    (_wb(r"\bdm for\b|\bdm us\b|\binbox for job\b"), 25, "\"DM for job\" pattern — real recruiters don't hire via direct message"),
    (_wb(r"\btyping job\b|\bdata entry job\b|\bcopy paste job\b"), 25, "Classic \"typing/data entry job\" scam template"),
    (_wb(r"\bjoin our telegram\b|\bjoin the group\b|\btelegram group\b"), 20, "Pushes you into an unofficial group chat, a common scam funnel"),
    (_wb(r"\btrainee kit\b|\bstarter kit\b|\btraining kit\b"), 25, "Asks you to buy a \"kit\" before starting — a known scam pattern"),
]

# Pay-for-a-fee needs both words nearby, not just "pay" anywhere
# (fixes the false positive on "Process Payment" / "Payment Gateway").
PAY_FEE_RE = _wb(r"\bpay\b.{0,40}\b(fee|deposit|registration|kit)\b|\b(fee|deposit|registration|kit)\b.{0,40}\bpay\b")

REFUNDABLE_FEE_RE = _wb(r"\brefundable\b.{0,40}\b(deposit|registration|fee)\b")


def check_text_rules(text, category=None):
    score = 0
    reasons = []

    if PAY_FEE_RE.search(text):
        score += 40
        reasons.append("Asks you to pay a fee/deposit before starting")

    if REFUNDABLE_FEE_RE.search(text):
        score += 30
        reasons.append("\"Refundable deposit/fee\" — a well-known scam device; the refund rarely happens")

    for pattern, points, reason in BASE_RULES:
        if pattern.search(text):
            score += points
            reasons.append(reason)

    if category and category in CATEGORY_KEYWORDS:
        for pattern, points, reason in CATEGORY_KEYWORDS[category]:
            if _wb(pattern).search(text):
                score += points
                reasons.append(reason)

    return score, reasons


def check_sender_domain(sender_email_domain, company_name):
    """Flags a claimed company whose sender uses a free personal
    email provider instead of their own domain."""
    if not sender_email_domain or not company_name:
        return 0, []

    if sender_email_domain.lower() in FREEMAIL_DOMAINS:
        return 25, [
            f"Sender uses a free email provider ({sender_email_domain}) despite claiming "
            f"to represent \"{company_name}\" — real companies use their own domain"
        ]

    return 0, []
