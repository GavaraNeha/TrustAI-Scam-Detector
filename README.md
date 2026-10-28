# 🛡️ TrustAI — Opportunity Checker

**Is this job or internship offer a scam, and is it even worth your time?**

TrustAI is a full-stack AI web app that checks job and internship messages (pasted text or a screenshot) and returns **two independent verdicts**: **Safety** (is it likely a scam?) and **Worth It** (does it add real resume value?). Every verdict comes with red flags, green flags, questions to ask the sender, web evidence, and a ready-to-send verification reply.

🔗 **Live demo:** https://trustai-scam-detector-2.onrender.com
*(Free Render tier: the first request after idle can take about 50 seconds to wake the server.)*

---

## 📌 Problem

Students and fresh graduates are constantly targeted by fake offers on WhatsApp, Telegram, SMS and email: "registration fees", "refundable deposits", fake HR Gmail accounts, and look-alike career sites such as `google-careers-india.xyz`. Keyword filters either miss these or flag legitimate offers, so TrustAI combines deterministic rules with live evidence and an LLM that reasons only over that evidence.

## ✨ Features

| Feature | What it does |
|---|---|
| 🧾 **Dual verdict** | Separate **Safety** and **Worth It** scores, because a safe offer can still be a waste of time |
| 📸 **Screenshot input** | Tesseract OCR reads offers pasted as images (WhatsApp, Telegram, email screenshots) |
| 🔒 **PII redaction** | Personal details are stripped before anything is sent to an LLM |
| 🚪 **Relevance gate** | Non-opportunity text (e.g. "lunch tomorrow?") is rejected before any API quota is spent |
| 📏 **Rule engine** | Word-boundary-safe scam patterns: fees, deposits, urgency, off-platform chat, free-mail recruiters |
| 🔗 **Link intelligence** | WHOIS domain age, VirusTotal reputation, and a check for domains that imitate the company name |
| 🌐 **Company research** | Tavily web search for fake-offer reports and the company's official domains |
| 🟢🔴 **Red and green flags** | Evidence-backed reasons on both sides, so a clean offer is explained, not just "no problems found" |
| 💬 **Verification reply** | One-click copyable message to send back to the recruiter |

## 🧠 How it works

```
Message or screenshot
        │
   OCR (Tesseract) ── PII redaction ── Relevance gate
        │
   LLM field extraction (company, links, sender, pay)
        │
   ┌────┴─────────────┬──────────────────┬─────────────────┐
   Rule engine     Company research    Link checks      Value scoring
   (regex, free-   (Tavily search,     (WHOIS age,      (pay, clarity,
   mail, fees)     official domains)   VirusTotal,      legitimacy)
                                       look-alike check)
   └────┬─────────────┴──────────────────┴─────────────────┘
        │
   Synthesizer (Groq/Gemini) reasons ONLY over gathered evidence
        │
   Deterministic guardrails (a hard scam signal can't be talked down)
        │
   Safety verdict + Worth-It verdict + flags + questions + reply
```

**Design decisions**
- **The LLM never invents evidence.** It sees only what the pipeline found, and "no data" results (WHOIS failed, VirusTotal queued) are treated as neutral, never as suspicious.
- **Impersonation is not guilt.** Articles about scammers impersonating a big company do not count against that company; only reports tied to the message's own red flags do.
- **Official-domain detection is conservative.** A link counts as official only if its exact registered domain appeared in the company's own search results (so `razorpay.com` passes and `razorpay-careers.in` fails).
- **Guardrails override the model.** A high rule score forces *Scam Likely*; a clean message on the company's own domain is capped at *Safe*.
- **Graceful degradation.** If the LLM is unavailable, the app falls back to a rule-based verdict instead of failing.

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Gunicorn |
| LLMs | Groq and Gemini (with model fallbacks) |
| Search | Tavily API |
| URL intelligence | VirusTotal API, python-whois |
| OCR | Tesseract via pytesseract and Pillow |
| Frontend | HTML, Tailwind CSS, vanilla JS |
| Deployment | Docker on Render |

## 📂 Project structure

```
TrustAI-Scam-Detector/
├── app.py                  # Flask app, /analyze endpoint
├── config.py               # env vars and model settings
├── ocr_utils.py            # screenshot → text
├── pipeline/
│   ├── orchestrator.py     # runs every stage in order
│   ├── ingest.py           # text/screenshot ingestion
│   ├── redact.py           # PII redaction
│   ├── relevance.py        # "is this an opportunity?" gate
│   ├── extractor.py        # LLM field extraction
│   ├── safety_rules.py     # regex scam rules
│   ├── url_intel.py        # WHOIS and VirusTotal
│   ├── company_intel.py    # Tavily company research
│   ├── domain_utils.py     # domain normalisation helpers
│   ├── value_scorer.py     # "worth it" context
│   ├── synthesizer.py      # final verdicts and guardrails
│   └── reply_generator.py  # verification reply
├── services/
│   ├── llm.py              # Groq/Gemini wrapper
│   ├── search.py           # Tavily wrapper
│   └── cache.py            # caches company lookups
├── templates/index.html    # UI
├── Dockerfile              # Python + Tesseract
└── requirements.txt
```

## 🚀 Run locally

**Prerequisites:** Python 3.11+, [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and on your PATH.

```bash
git clone https://github.com/GavaraNeha/TrustAI-Scam-Detector.git
cd TrustAI-Scam-Detector
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys
python app.py
```

Open http://localhost:5000.

**Environment variables** (see `.env.example`):

| Variable | Used for |
|---|---|
| `GROQ_API_KEY` | LLM (primary) |
| `GEMINI_API_KEY` | LLM (fallback) |
| `TAVILY_API_KEY` | Company web search |
| `VIRUSTOTAL_API_KEY` | Link reputation |
| `WHOIS_API_KEY` | Domain lookups (optional) |

`SETUP.md` and `test_apis.py` help check that each key works.

## ☁️ Deploy (Render + Docker)

1. Push the repo to GitHub.
2. On Render: **New → Web Service**, pick the repo, set **Language: Docker**.
3. Add the environment variables above.
4. Deploy. The `Dockerfile` installs Tesseract and starts Gunicorn on `$PORT`.

## 🧪 Example results

| Input | Safety | Worth It |
|---|---|---|
| "Pay Rs 999 registration fee… WhatsApp immediately!" (fake Amazon job) | 🔴 Scam Likely 95% | Weak |
| "Refundable deposit… contact hr.infosys.careers@gmail.com" | 🔴 Scam Likely 85–90% | Weak |
| Apply at `google-careers-india.xyz` | 🔴 Scam Likely 80% | Weak |
| Real Razorpay internship, `razorpay.com/jobs`, "no fees" | 🟢 Safe 0–5% | Strong 80% |
| "Are we still meeting for lunch?" | Rejected: not an opportunity | — |

## ⚠️ Limitations

- It gives **risk signals, not legal proof**. Always verify through the company's official careers page.
- Free API tiers apply: VirusTotal allows 4 requests/minute, and Tavily has a monthly credit cap.
- A brand-new legitimate company with no web presence may come back as *Can't Verify* instead of *Safe*.
- Screenshot accuracy depends on image quality.

## 🔮 Roadmap

- [ ] Hindi, Telugu and Tamil support
- [ ] Browser extension for WhatsApp Web and Gmail
- [ ] Feedback loop ("was this right?") to tune the rules
- [ ] Public JSON API
- [ ] Evaluation set with precision/recall tracking

## 👩‍💻 About

Built by **Gavara Neha**, B.Tech in AI & Machine Learning, Aditya University.
[GitHub](https://github.com/GavaraNeha)

## 📄 License

MIT. See [LICENSE](LICENSE).

---

*Built to protect job seekers from online fraud, one message at a time.*
