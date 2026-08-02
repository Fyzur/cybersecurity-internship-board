"""Scraper for Okta's careers site (okta.com/careers).

Okta's job board is backed by Greenhouse. Confirmed by hitting the public
Greenhouse Job Board API directly (no HTML parsing needed):
    https://boards-api.greenhouse.io/v1/boards/okta/jobs

robots.txt for boards-api.greenhouse.io imposes no restrictions on this
read-only API endpoint (it is the same data Greenhouse serves to Okta's own
careers page via client-side JS).
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing

COMPANY_NAME = "Okta"
BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/okta/jobs?content=true"


def fetch_internships():
    resp = requests.get(BOARD_URL, timeout=20)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])

    today = datetime.now(timezone.utc).date().isoformat()
    results = []
    for job in jobs:
        title = job.get("title", "")
        content = job.get("content", "")
        if not is_cyber_listing(title, content):
            continue

        # Greenhouse's list endpoint doesn't expose an original "first posted"
        # date, only updated_at. We use it as the best available proxy.
        updated_at = job.get("updated_at", "")
        date_posted = updated_at[:10] if updated_at else today

        results.append({
            "company": COMPANY_NAME,
            "title": title,
            "location": job.get("location", {}).get("name") or "Unknown",
            "url": job.get("absolute_url", ""),
            "date_posted": date_posted,
            "date_scraped": today,
        })
    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
