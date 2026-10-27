"""
Checks a URL two ways:
- Domain age via WHOIS (no API key needed).
- VirusTotal URL reputation (free tier: 4 requests/min).

Every "no data" outcome (queued, skipped, error, WHOIS failure) is
NEUTRAL. Only a real finding (young domain, malicious detections)
counts against a link, and that is decided in the orchestrator.
"""
import base64
from datetime import datetime, timezone

import requests
import whois

import config
from pipeline.domain_utils import normalise_url, host_of


def check_domain_age(url):
    try:
        domain = host_of(url).replace("www.", "")
        info = whois.whois(domain)
        creation = info.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if not creation:
            return {"domain": domain, "age_days": None, "note": "Creation date not available"}

        if creation.tzinfo is None:
            creation = creation.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - creation).days
        return {"domain": domain, "age_days": int(age_days), "note": None}
    except Exception as e:
        print(f"[WHOIS] {e}")
        return {"domain": None, "age_days": None, "note": f"WHOIS lookup failed: {e}"}


def check_virustotal(url):
    if not config.VIRUSTOTAL_API_KEY:
        return {"status": "skipped", "note": "No VIRUSTOTAL_API_KEY set"}

    url = normalise_url(url)
    headers = {"x-apikey": config.VIRUSTOTAL_API_KEY}
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")

    try:
        existing = requests.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=15
        )
        if existing.status_code == 200:
            stats = existing.json()["data"]["attributes"]["last_analysis_stats"]
            return {"status": "analyzed", "stats": stats}

        submit = requests.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url},
            timeout=15,
        )
        submit.raise_for_status()
        return {"status": "queued", "note": "No reputation data yet (neutral, not a warning sign)"}

    except Exception as e:
        print(f"[VirusTotal] {e}")
        return {"status": "error", "note": str(e)}


def check_url(url, official=False):
    """official=True skips VirusTotal to save free-tier quota."""
    if official:
        vt = {"status": "skipped", "note": "Matches the company's official domain"}
    else:
        vt = check_virustotal(url)
    return {
        "url": url,
        "domain_age": check_domain_age(url),
        "virustotal": vt,
    }
