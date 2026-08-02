"""Scraper for Microsoft's careers site (careers.microsoft.com).

Microsoft exposes a public JSON search API. We use the newer jobs API endpoint
and search for security-related roles, then apply the shared keyword filter.

NOTE: Microsoft's API endpoint and response shape can change. If you start
getting errors, open careers.microsoft.com in a browser, search for "security",
watch the Network tab for the JSON API call, and update SEARCH_URL below.
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "Microsoft"
SEARCH_URL = "https://jobs.careers.microsoft.com/global/en/search"
APPLY_BASE = "https://jobs.careers.microsoft.com/global/en/job"
PAGE_SIZE = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-board-scraper/1.0)",
    "Accept": "application/json",
}


def _fetch_page(page: int) -> dict:
    params = {
        "q": "security",
        "pg": page,
        "pgSz": PAGE_SIZE,
        "o": "Date",
        "flt": "true",
        "lc": "en_us",
    }
    resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_internships():
    today = datetime.now(timezone.utc).date().isoformat()
    results = []
    page = 1

    while True:
        data = _fetch_page(page)

        # Try both known response shapes.
        # Shape 1: {"operationResult": {"result": {"jobs": [...], "totalCount": N}}}
        # Shape 2: {"value": [...], "totalCount": N}
        jobs = (
            data.get("operationResult", {}).get("result", {}).get("jobs")
            or data.get("value")
            or []
        )
        total = (
            data.get("operationResult", {}).get("result", {}).get("totalCount")
            or data.get("totalCount")
            or 0
        )

        if not jobs:
            break

        for job in jobs:
            title = job.get("title", "")
            description = (job.get("properties") or {}).get("description", "")
            if not is_cyber_listing(title, description):
                continue

            job_id = job.get("jobId", "")
            url = f"{APPLY_BASE}/{job_id}" if job_id else APPLY_BASE

            city = job.get("city", "")
            state = job.get("stateOrProvince", "")
            country = job.get("country", "")
            location = ", ".join(p for p in [city, state, country] if p) or "Unknown"

            date_posted = (job.get("startDate") or job.get("postingDate") or today)[:10]

            results.append(make_listing(
                company=COMPANY_NAME,
                title=title,
                location=location,
                url=url,
                date_posted=date_posted,
                date_scraped=today,
            ))

        if page * PAGE_SIZE >= total:
            break
        page += 1

    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
