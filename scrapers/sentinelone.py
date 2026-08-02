"""Scraper for SentinelOne's careers site (sentinelone.com/careers).

SentinelOne uses Lever. Public JSON API (no HTML parsing needed):
    https://api.lever.co/v0/postings/sentinelone?mode=json

NOTE: If this returns 404, check sentinelone.com/careers in a browser's Network
tab for an API call to lever.co, greenhouse.io, or workday to get the current slug.
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "SentinelOne"
LEVER_URL = "https://api.lever.co/v0/postings/sentinelone?mode=json"


def fetch_internships():
    resp = requests.get(LEVER_URL, timeout=20)
    resp.raise_for_status()
    jobs = resp.json()

    today = datetime.now(timezone.utc).date().isoformat()
    results = []
    for job in jobs:
        title = job.get("text", "")
        description = job.get("descriptionPlain", "") or job.get("description", "")
        if not is_cyber_listing(title, description):
            continue

        created_ms = job.get("createdAt", 0)
        if created_ms:
            from datetime import datetime as dt
            date_posted = dt.utcfromtimestamp(created_ms / 1000).date().isoformat()
        else:
            date_posted = today

        location = job.get("categories", {}).get("location", "") or "Unknown"
        apply_url = job.get("hostedUrl", job.get("applyUrl", ""))

        results.append(make_listing(
            company=COMPANY_NAME,
            title=title,
            location=location,
            url=apply_url,
            date_posted=date_posted,
            date_scraped=today,
        ))
    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
