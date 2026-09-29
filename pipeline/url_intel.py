"""
Checks a URL two ways:
- Domain age via WHOIS (no API key needed) -- very new domains are
  a common scam signal.
- VirusTotal URL reputation (free tier: 4 requests/min, 500/day,
  non-commercial use only -- fine for a student project, not for
  a monetized product).

VirusTotal's free tier is asynchronous for URLs it hasn't seen
before: submitting a new URL queues an analysis that isn't ready
instantly. This code submits it and reports "queued, check back
later" rather than pretending to have a verdict it doesn't have.
"""
import base64
import time
import requests
import whois

import config


def check_domain_age(url):
    try:
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        info = whois.whois(domain)
        creation = info.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if not creation:
            return {"domain": domain, "age_days": None, "note": "Creation date not available"}

        age_days = (time.time() - creation.timestamp()) / 86400
        return {"domain": domain, "age_days": int(age_days), "note": None}
    except Exception as e:
        return {"domain": None, "age_days": None, "note": f"WHOIS lookup failed: {e}"}


def check_virustotal(url):
    if not config.VIRUSTOTAL_API_KEY:
        return {"status": "skipped", "note": "No VIRUSTOTAL_API_KEY set"}

    headers = {"x-apikey": config.VIRUSTOTAL_API_KEY}
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")

    try:
        # Try an existing report first (free, no quota cost for a cache hit).
        existing = requests.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=15
        )
        if existing.status_code == 200:
            stats = existing.json()["data"]["attributes"]["last_analysis_stats"]
            return {"status": "analyzed", "stats": stats}

        # Not seen before -- submit it. Result won't be ready instantly.
        submit = requests.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url},
            timeout=15,
        )
        submit.raise_for_status()
        return {"status": "queued", "note": "First-time URL, VirusTotal is still analyzing it"}

    except Exception as e:
        return {"status": "error", "note": str(e)}


def check_url(url):
    return {
        "url": url,
        "domain_age": check_domain_age(url),
        "virustotal": check_virustotal(url),
    }
