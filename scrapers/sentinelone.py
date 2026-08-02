"""Scraper for SentinelOne's careers site (sentinelone.com/careers).

SentinelOne uses Greenhouse. Public JSON API (no HTML parsing needed):
    https://boards-api.greenhouse.io/v1/boards/sentinelone/jobs

robots.txt for boards-api.greenhouse.io permits read-only access to these
board endpoints.
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "SentinelOne"
BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/sentinelone/jobs?content=true"


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

        updated_at = job.get("updated_at", "")
        date_posted = updated_at[:10] if updated_at else today

        results.append(make_listing(
            company=COMPANY_NAME,
            title=title,
            location=job.get("location", {}).get("name"),
            url=job.get("absolute_url", ""),
            date_posted=date_posted,
            date_scraped=today,
        ))
    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
