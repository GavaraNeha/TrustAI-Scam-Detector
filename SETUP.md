# TrustAI v3 — Setup

## 1. Install dependencies
```
pip install -r requirements.txt
```

## 2. Set up your .env
Copy `.env.example` to `.env` and paste in your real keys:
```
GROQ_API_KEY=...
GEMINI_API_KEY=...
TAVILY_API_KEY=...
VIRUSTOTAL_API_KEY=...
```
Add `.env` to your `.gitignore` — never commit real API keys.

## 3. Tesseract (for screenshot OCR)
Same as before — install the actual Tesseract program (not just the pip
package). If it's not on your Windows PATH, edit the path in `ocr_utils.py`.

## 4. Run
```
python app.py
```

## What changed from v2
- Real LLM-based extraction and reasoning instead of only keyword rules
  (rules still run, but as one input to the final verdict, not the whole thing)
- Two separate verdicts: Safety (is it a scam) and Worth It (does it add
  resume value even if it's not a scam)
- A relevance gate: irrelevant text (like a diagram) gets told plainly
  it isn't an opportunity message, instead of getting a fake risk score
- Word-boundary matching fixes the "Payment Gateway" false positive
  from matching "pay" as a substring
- URL checking: domain age (WHOIS, free) + VirusTotal reputation
- Company research (Tavily search) is cached in data/cache.sqlite3 so
  repeat lookups don't burn free-tier quota

## Known limitations, honestly
- VirusTotal's free tier is asynchronous for URLs it hasn't seen before —
  a brand-new URL will show "queued" the first time, not an instant verdict.
- Gemini is the fallback LLM only; on its free tier Google may use your
  prompts to improve their products. The redact.py step strips emails/phones
  before anything reaches either LLM, but be mindful of what you paste.
- There's no free official registry check (like India's MCA for a CIN
  number) — company legitimacy leans on search evidence, not a database.
- Rate limits change over time on all four free tiers — if a request
  suddenly fails, check your provider's dashboard before assuming the
  code is broken.
