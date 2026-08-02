"""Scraper for Microsoft's careers site (careers.microsoft.com).

Microsoft's JSON search API is at gcsservices.careers.microsoft.com. The SSL
cert is issued for a CDN hostname (Azure CDN), causing a hostname mismatch when
connecting directly. We disable certificate verification for this host only;
the data itself is public read-only job listings so there is no credential risk.

NOTE: If results stop appearing, open careers.microsoft.com in a browser, search
for "security", and watch the Network tab for the gcsservices API call to confirm
the URL and params are still correct.
"""
import urllib3
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

# Suppress the InsecureRequestWarning we generate below for this one host.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COMPANY_NAME = "Microsoft"
SEARCH_URL = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
APPLY_BASE = "https://careers.microsoft.com/us/en/job"
PAGE_SIZE = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-board-scraper/1.0)",
    "Accept": "application/json",
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
    # verify=False: Azure CDN hostname mismatch — see module docstring.
    resp = requests.get(
        SEARCH_URL, params=params, headers=HEADERS, timeout=20, verify=False
    )
    resp.raise_for_status()
    return resp.json()


def fetch_internships():
    today = datetime.now(timezone.utc).date().isoformat()
    results = []
    page = 1

    while True:
        data = _fetch_page(page)
        result = data.get("operationResult", {}).get("result", {})
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

            city = job.get("city", "")
            state = job.get("stateOrProvince", "")
            country = job.get("country", "")
            location = ", ".join(p for p in [city, state, country] if p) or "Unknown"
            date_posted = (job.get("startDate") or today)[:10]

            results.append(make_listing(
                company=COMPANY_NAME,
                title=title,
                location=location,
                url=url,
                date_posted=date_posted,
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
