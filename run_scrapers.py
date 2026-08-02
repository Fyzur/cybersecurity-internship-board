"""Run every registered company scraper and write data/internships.json.

Each scraper module must expose fetch_internships() -> list[dict] and must
never let one company's failure take down the rest of the run.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from scrapers.crowdstrike import fetch_internships as crowdstrike_fetch
from scrapers.microsoft import fetch_internships as microsoft_fetch
from scrapers.okta import fetch_internships as okta_fetch
from scrapers.rapid7 import fetch_internships as rapid7_fetch
from scrapers.sentinelone import fetch_internships as sentinelone_fetch

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "internships.json"

# company name -> fetch function. Add one entry per scraper module.
SCRAPERS = {
    "CrowdStrike": crowdstrike_fetch,
    "Microsoft": microsoft_fetch,
    "Okta": okta_fetch,
    "Rapid7": rapid7_fetch,
    "SentinelOne": sentinelone_fetch,
}

REQUEST_DELAY_SECONDS = 1.5


def main():
    all_listings = []
    failures = []

    names = list(SCRAPERS.items())
    for i, (name, fetch) in enumerate(names):
        try:
            listings = fetch()
            print(f"[{name}] found {len(listings)} matching internship(s)")
            all_listings.extend(listings)
        except Exception as exc:
            print(f"[{name}] FAILED: {exc}", file=sys.stderr)
            failures.append({"company": name, "error": str(exc)})

        if i < len(names) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    all_listings.sort(key=lambda x: x["date_posted"], reverse=True)

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "internships": all_listings,
        "failed_scrapers": failures,
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"\nWrote {len(all_listings)} internship(s) to {DATA_PATH}")
    if failures:
        print(f"{len(failures)} scraper(s) failed: {[f['company'] for f in failures]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
