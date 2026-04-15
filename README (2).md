# 💼 Job Listings Aggregator

Scrapes job listings from **Internshala**, **Naukri**, and **Shine** using Playwright.  
Handles basic anti-bot measures, deduplicates results, and saves to JSON + CSV.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
python job_aggregator.py
```

## Features

- **Headless browser** via Playwright — handles JS-rendered pages
- **User-agent rotation** — picks a random browser identity each run
- **Random delays** between requests — mimics real human browsing
- **Deduplication** — removes same job listed on multiple sites
- **CLI filter** — search saved results by title, location, or source

## How to use

**Option 1 — Scrape fresh jobs**
```
Choice: 1
Keyword : python developer
Location: bangalore
```

**Option 2 — Filter saved jobs**
```
Choice: 2
Filter by title keyword: python
Filter by location     : bangalore
Filter by source       : Naukri
```

## Output files

| File | What's in it |
|------|-------------|
| `jobs.json` | All jobs as structured JSON |
| `jobs.csv`  | Same data, spreadsheet-friendly |

## Anti-bot techniques used

| Technique | Why |
|-----------|-----|
| Headless Chromium | Renders JavaScript like a real browser |
| User-agent rotation | Different browser fingerprint each run |
| Random delay between requests | Doesn't look like an automated bot |
| Per-site browser context | Isolated cookies/sessions |

## Libraries used
- `playwright` — browser automation
