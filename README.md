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

| Company | ATS | API endpoint | Notes |
|---|---|---|---|
| Okta | Greenhouse | `boards-api.greenhouse.io/v1/boards/okta/jobs` | Working ✅ |
| Rapid7 | Greenhouse | `boards-api.greenhouse.io/v1/boards/rapid7/jobs` | Working ✅ |
| SentinelOne | Greenhouse | `boards-api.greenhouse.io/v1/boards/sentinelone/jobs` | Working ✅ |
| CrowdStrike | Workday | `crowdstrike.wd5.myworkdayjobs.com/wday/cxs/crowdstrike/crowdstrikecareers/jobs` | POST-based JSON API. Flag: Workday tenant path may drift — check Network tab if 404s appear. |
| Microsoft | Custom | `gcsservices.careers.microsoft.com/search/api/v1/search` | GET JSON API. Flag: response shape may change — watch for KeyErrors in logs. |

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
