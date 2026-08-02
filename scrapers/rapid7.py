"""Scraper for Rapid7's careers site (rapid7.com/careers).

STATUS: BROKEN, not easily fixable. Rapid7 moved off Workday to a Radancy/
Clinch-hosted site (careers.rapid7.com). Its job-search endpoint sits behind
AWS WAF Bot Control - plain HTTP requests get a "challenge" response (empty
202) instead of data. Individual job pages are fetchable and expose a
JobPosting JSON-LD block, but there is no public way to enumerate the full
job list without going through the WAF-gated search (the site's sitemap.xml
only lists a handful of recently-changed pages, not all open jobs). We do not
attempt to solve/evade the WAF challenge. This is left in place, still
pointing at the old (now-dead) Workday URL, so it fails loudly and predictably
via `failed_scrapers` rather than silently returning nothing - see README for
details, and revisit if Rapid7 ever exposes a public jobs API again.
"""
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "Rapid7"
WORKDAY_URL = (
    "https://rapid7.wd5.myworkdayjobs.com/wday/cxs/rapid7/rapid7-Careers/jobs"
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
            if not is_cyber_listing(title):
                continue

            external_path = job.get("externalPath", "")
            base = "https://rapid7.wd5.myworkdayjobs.com/rapid7-Careers"
            url = base + external_path if external_path else base

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
