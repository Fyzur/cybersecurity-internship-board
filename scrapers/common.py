"""Shared helpers used by every company scraper module."""
import re

# Keywords that mark a listing as cybersecurity-related.
KEYWORDS = [
    "security",
    "cyber",
    "soc",
    "grc",
    "iam",
    "identity",
    "threat",
    "incident response",
    "penetration test",
    "siem",
    "vulnerability",
]

_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in KEYWORDS) + r")\b", re.IGNORECASE
)


def is_cyber_listing(title, description=""):
    """True if title+description mentions a cyber keyword. All seniority levels match."""
    return bool(_KEYWORD_PATTERN.search(f"{title} {description}"))


def make_listing(company, title, location, url, date_posted, date_scraped):
    return {
        "company": company,
        "title": title,
        "location": location or "Unknown",
        "url": url,
        "date_posted": date_posted,
        "date_scraped": date_scraped,
    }
