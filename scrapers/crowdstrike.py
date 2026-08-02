"""Scraper for CrowdStrike's careers site (crowdstrike.com/careers).

CrowdStrike uses Workday. The public jobs API is available at:
    https://crowdstrike.wd5.myworkdayjobs.com/wday/cxs/crowdstrike/crowdstrikecareers/jobs

Workday exposes a POST-based JSON search API. We POST a minimal payload and
paginate through results. No HTML parsing needed.

NOTE: Workday tenant/path may drift over time. If this scraper starts returning
404s, open crowdstrike.com/careers in a browser, watch the Network tab for a
POST to a `*/wday/cxs/*/jobs` URL, and update WORKDAY_URL below.
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "CrowdStrike"
WORKDAY_URL = (
    "https://crowdstrike.wd5.myworkdayjobs.com/wday/cxs/crowdstrike/"
    "crowdstrikecareers/jobs"
)
PAGE_SIZE = 20
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; internship-board-scraper/1.0)",
}


def _fetch_page(offset: int) -> dict:
    payload = {
        "appliedFacets": {},
        "limit": PAGE_SIZE,
        "offset": offset,
        "searchText": "",
    }
    resp = requests.post(WORKDAY_URL, json=payload, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_internships():
    today = datetime.now(timezone.utc).date().isoformat()
    results = []
    offset = 0

    while True:
        data = _fetch_page(offset)
        job_postings = data.get("jobPostings", [])
        if not job_postings:
            break

        for job in job_postings:
            title = job.get("title", "")
            # Workday list endpoint has no description; filter on title only.
            if not is_cyber_listing(title):
                continue

            # Workday returns a relative path; build the absolute apply URL.
            external_path = job.get("externalPath", "")
            base = "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers"
            url = base + external_path if external_path else base

            # Workday list API doesn't expose a posted date reliably.
            posted = job.get("postedOn", "") or today

            results.append(make_listing(
                company=COMPANY_NAME,
                title=title,
                location=job.get("locationsText", "") or job.get("location", ""),
                url=url,
                date_posted=posted,
                date_scraped=today,
            ))

        total = data.get("total", 0)
        offset += PAGE_SIZE
        if offset >= total:
            break

    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
