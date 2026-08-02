"""Scraper for Microsoft's careers site (careers.microsoft.com).

Microsoft exposes a public JSON search API:
    GET https://gcsservices.careers.microsoft.com/search/api/v1/search

We search for "security" (broad enough to catch cyber, IAM, SOC, etc.) and
then apply the shared keyword filter on the returned title + description.

NOTE: Microsoft's API structure may change. If you start getting KeyErrors or
empty results, open careers.microsoft.com in a browser, search for "security
intern", watch the Network tab for the gcsservices call, and update
SEARCH_URL / response parsing below.
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "Microsoft"
SEARCH_URL = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
APPLY_BASE = "https://careers.microsoft.com/us/en/job"
PAGE_SIZE = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-board-scraper/1.0)",
}


def _fetch_page(page: int) -> dict:
    params = {
        "q": "security",
        "lc": "en_us",
        "pg": page,
        "pgSz": PAGE_SIZE,
        "o": "Date",
        "flt": "true",
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
        # Response shape: {"operationResult": {"result": {"jobs": [...], "totalCount": N}}}
        operation = data.get("operationResult", {})
        result = operation.get("result", {})
        jobs = result.get("jobs", [])

        if not jobs:
            break

        for job in jobs:
            title = job.get("title", "")
            description = (job.get("properties") or {}).get("description", "")
            if not is_cyber_listing(title, description):
                continue

            job_id = job.get("jobId", "")
            url = f"{APPLY_BASE}/{job_id}" if job_id else APPLY_BASE

            # Build location string from available fields.
            city = job.get("city", "")
            state = job.get("stateOrProvince", "")
            country = job.get("country", "")
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) or "Unknown"

            start_date = job.get("startDate", "") or today

            results.append(make_listing(
                company=COMPANY_NAME,
                title=title,
                location=location,
                url=url,
                date_posted=start_date[:10],
                date_scraped=today,
            ))

        total = result.get("totalCount", 0)
        if page * PAGE_SIZE >= total:
            break
        page += 1

    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
