"""Scraper for Microsoft's careers site (careers.microsoft.com).

Microsoft moved its careers platform to apply.careers.microsoft.com (Eightfold).
The site's own search API (/api/apply/v2/jobs) returns 403 "Not authorized for
PCSX" for unauthenticated requests, even though robots.txt allows crawling it -
it appears to require a signed-in session. Instead, we use the public job
sitemap (robots.txt: `Allow: /careers`), which lists every open job URL, and
read the standard schema.org JobPosting JSON-LD block off each job page - the
same structured data Microsoft publishes for search engines.

NOTE: If this stops finding jobs, open apply.careers.microsoft.com/careers in a
browser and confirm SITEMAP_URL below still resolves and still contains
<script type="application/ld+json"> JobPosting blocks on individual job pages.
"""
import json
import re
import time
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "Microsoft"
SITEMAP_URL = "https://apply.careers.microsoft.com/careers/sitemap.xml"
REQUEST_DELAY_SECONDS = 0.3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-board-scraper/1.0)",
}

_JOB_URL_RE = re.compile(r"<loc>(https://apply\.careers\.microsoft\.com/careers/job/[^<]+)</loc>")
_LD_JSON_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL
)


def _candidate_job_urls():
    resp = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    urls = []
    for url in _JOB_URL_RE.findall(resp.text):
        # The URL slug is "<job-id>-<title words>-<location words>". Pre-filter
        # on it (hyphens -> spaces) so we only fetch job pages worth reading.
        slug = url.rsplit("/careers/job/", 1)[-1].split("?", 1)[0]
        pseudo_title = slug.replace("-", " ")
        if is_cyber_listing(pseudo_title):
            urls.append(url)
    return urls


def _format_one_location(place: dict) -> str:
    address = (place or {}).get("address", {})
    locality = address.get("addressLocality", "")
    region = (address.get("addressRegion", "") or "").split(",")[0]
    country = (address.get("addressCountry", {}) or {}).get("name", "")
    return ", ".join(p for p in [locality, region, country] if p)


def _format_location(job_location) -> str:
    # jobLocation is a single Place for single-location jobs, a list for
    # multi-location postings.
    places = job_location if isinstance(job_location, list) else [job_location]
    formatted = [_format_one_location(p) for p in places]
    return "; ".join(f for f in formatted if f)


def fetch_internships():
    today = datetime.now(timezone.utc).date().isoformat()
    results = []

    job_urls = _candidate_job_urls()

    for url in job_urls:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        time.sleep(REQUEST_DELAY_SECONDS)
        if not resp.ok:
            continue

        match = _LD_JSON_RE.search(resp.text)
        if not match:
            continue

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        title = data.get("title", "")
        description = data.get("description", "")
        if not is_cyber_listing(title, description):
            continue

        date_posted = (data.get("datePosted") or today)[:10]

        results.append(make_listing(
            company=COMPANY_NAME,
            title=title,
            location=_format_location(data.get("jobLocation")),
            url=url,
            date_posted=date_posted,
            date_scraped=today,
        ))

    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
