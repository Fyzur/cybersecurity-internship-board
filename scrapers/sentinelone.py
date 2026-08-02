"""Scraper for SentinelOne's careers site (sentinelone.com/jobs).

SentinelOne no longer uses Workday - the old WORKDAY_URL now returns 401. Their
careers page (a Next.js app) embeds the full open-jobs list (Greenhouse job
data, server-rendered) directly in the page's React Server Components payload
(the `self.__next_f.push([1, "..."])` script chunks). We fetch the page and
pull the `"jobs":[...]` array out of that payload instead of hitting an ATS API
directly, since no public API endpoint is exposed.

NOTE: If this stops finding jobs, open sentinelone.com/jobs in a browser, view
source, and confirm a `self.__next_f.push` chunk still contains a `"jobs":[`
array with `absolute_url`/`title`/`location` fields.
"""
import json
import re
from datetime import datetime, timezone

import requests

from .common import is_cyber_listing, make_listing

COMPANY_NAME = "SentinelOne"
JOBS_PAGE_URL = "https://www.sentinelone.com/jobs/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; internship-board-scraper/1.0)",
}

_NEXT_F_CHUNK_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', re.DOTALL)


def _extract_jobs_array(decoded_chunk: str):
    """Bracket-match the `"jobs":[...]` array out of a decoded RSC payload string."""
    marker = '"jobs":['
    idx = decoded_chunk.find(marker)
    if idx == -1:
        return None

    start = idx + len('"jobs":')
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(decoded_chunk)):
        ch = decoded_chunk[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return decoded_chunk[start:i + 1]
    return None


def _fetch_jobs():
    resp = requests.get(JOBS_PAGE_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    for raw_chunk in _NEXT_F_CHUNK_RE.findall(resp.text):
        if "absolute_url" not in raw_chunk:
            continue
        # The chunk is a JSON-string-escaped blob; wrap in quotes and decode
        # via json.loads to unescape \" and \uXXXX sequences properly.
        decoded = json.loads('"' + raw_chunk + '"')
        jobs_json = _extract_jobs_array(decoded)
        if jobs_json:
            return json.loads(jobs_json)
    return []


def fetch_internships():
    today = datetime.now(timezone.utc).date().isoformat()
    results = []

    for job in _fetch_jobs():
        title = job.get("title", "")
        if not is_cyber_listing(title):
            continue

        location = (job.get("location") or {}).get("name", "")
        date_posted = (job.get("first_published") or today)[:10]

        results.append(make_listing(
            company=COMPANY_NAME,
            title=title,
            location=location,
            url=job.get("absolute_url", ""),
            date_posted=date_posted,
            date_scraped=today,
        ))

    return results


if __name__ == "__main__":
    for listing in fetch_internships():
        print(listing)
