# Cybersecurity Internship Board

Aggregates active cybersecurity roles (internship through senior) from company
career pages into a searchable static site. No backend, no database — a
scheduled scraper writes `data/internships.json`, the static frontend renders it.

## Stack

- **Scrapers**: Python (`requests`; `beautifulsoup4`/`playwright` added only for
  companies that need HTML parsing instead of a JSON ATS endpoint)
- **Data**: `data/internships.json`, committed to the repo
- **Frontend**: static HTML/CSS/vanilla JS in `site/`
- **Automation**: GitHub Actions — scrapes every 8 hours, commits updated data,
  deploys `site/` to GitHub Pages (see `.github/workflows/scrape.yml`)
- **Hosting**: GitHub Pages

## Status

- [x] Repo structure (`scrapers/`, `data/`, `site/`)
- [x] First scraper built and tested end-to-end: **Okta** (Greenhouse ATS)
- [x] Static frontend: search, company filter, sort by date, last-updated stamp
- [x] Remaining 4 proof-of-concept scrapers: Rapid7, SentinelOne, CrowdStrike, Microsoft
- [x] GitHub Actions scheduled workflow (`.github/workflows/scrape.yml`)
- [ ] GitHub Pages deploy — **one-time setup required** (see below)

## One-time GitHub Pages setup

1. Push this repo to GitHub.
2. In the repo → **Settings → Pages**, set Source to **GitHub Actions**.
3. Trigger the workflow manually: **Actions → Scrape & Deploy → Run workflow**.
4. The live URL will appear in the workflow run summary and in Settings → Pages.

## Scraper notes / ATS findings

| Company | ATS | Status | Notes |
|---|---|---|---|
| Okta | Greenhouse | ✅ Working | `boards-api.greenhouse.io/v1/boards/okta/jobs` |
| CrowdStrike | Workday | ✅ Working | `crowdstrike.wd5.myworkdayjobs.com/wday/cxs/crowdstrike/crowdstrikecareers/jobs` |
| SentinelOne | Greenhouse (custom UI) | ✅ Working | They moved off Workday to a Next.js careers page (`sentinelone.com/jobs`) that server-renders the full Greenhouse job list into the page's RSC payload. No public API — `scrapers/sentinelone.py` extracts the embedded `"jobs":[...]` array instead. |
| Microsoft | Eightfold (`apply.careers.microsoft.com`) | ✅ Working | Moved off the old `gcsservices` endpoint. Their search API (`/api/apply/v2/jobs`) 403s for unauthenticated requests, so `scrapers/microsoft.py` instead reads the public `/careers/sitemap.xml` job list and parses the `JobPosting` JSON-LD block on each matching job page (same structured data they publish for search engines). |
| Rapid7 | Radancy/Clinch (`careers.rapid7.com`) | ❌ Blocked | The Workday board is gone; the new job-search endpoint sits behind AWS WAF Bot Control (returns an empty 202 "challenge" response to plain HTTP clients). Individual job pages *are* fetchable and expose `JobPosting` JSON-LD, but there's no public way to enumerate all open jobs without going through the WAF-gated search — the only sitemap available is a small "recently changed pages" list, not the full job board. Not fixed: doing so would require solving/evading the bot challenge, which we intentionally don't do. `run_scrapers.py` reports it in `failed_scrapers` and moves on. |

Companies not yet checked: Google, Amazon, Apple, IBM, Cisco, Palo Alto Networks,
Fortinet, CyberArk, Tenable, Splunk, Mandiant/Google Cloud Security.

## Keyword filter

A listing counts as a cybersecurity role if its title or description contains
one of: `security, cyber, soc, grc, iam, identity, threat, incident response,
penetration test, siem, vulnerability` (case-insensitive, word-boundary matched —
see `scrapers/common.py`).

## Running locally

```bash
pip install -r requirements.txt
python run_scrapers.py                          # writes data/internships.json
cp data/internships.json site/internships.json  # make data available to the frontend
python -m http.server 8000 --directory site     # serve the site
# open http://localhost:8000
```

## Adding a new company scraper

1. Check the company's careers page in a browser's Network tab for a JSON API
   call (Greenhouse: `boards-api.greenhouse.io/v1/boards/<token>/jobs`,
   Lever: `api.lever.co/v0/postings/<token>`, Workday: POST to
   `<company>.wd*.myworkdayjobs.com/wday/cxs/.../jobs`). Check `robots.txt` first.
2. Create `scrapers/<company>.py` exposing `fetch_internships() -> list[dict]`,
   using `scrapers.common.is_cyber_listing()` for filtering and
   `scrapers.common.make_listing()` for the output shape.
3. Register it in `SCRAPERS` in `run_scrapers.py`.
4. Run `python run_scrapers.py` locally to confirm it works. Failures are caught
   at the orchestrator level and logged to `failed_scrapers` in the JSON output —
   one broken scraper won't take down the rest.
