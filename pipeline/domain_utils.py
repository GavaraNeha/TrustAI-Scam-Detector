"""Small domain helpers shared by the pipeline."""
import re
from urllib.parse import urlparse

_SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "edu", "nic"}


def normalise_url(url):
    url = (url or "").strip()
    if not url:
        return url
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    return url


def host_of(url):
    try:
        return (urlparse(normalise_url(url)).hostname or "").lower()
    except Exception:
        return ""


def registered_domain(url_or_host):
    parts = [p for p in host_of(url_or_host).split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    if len(parts[-1]) == 2 and parts[-2] in _SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def domain_label(domain):
    parts = [p for p in (domain or "").split(".") if p]
    if not parts:
        return ""
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in _SECOND_LEVEL:
        return parts[-3]
    return parts[0]


def company_slugs(name):
    """'Infosys BPO' -> {'infosysbpo', 'infosys'}"""
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    if not words:
        return set()
    slugs = {"".join(words)}
    if len(words[0]) >= 4:
        slugs.add(words[0])
    return slugs
