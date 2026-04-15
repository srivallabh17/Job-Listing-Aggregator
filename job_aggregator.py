import asyncio
import json
import csv
import os
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright


# ── settings ──────────────────────────────────────────────────────────────────
OUTPUT_JSON = "jobs.json"
OUTPUT_CSV  = "jobs.csv"

# Rotate user-agents so we don't look like a bot
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
]

# ── random delay helper ───────────────────────────────────────────────────────

def random_delay(min_sec=1.5, max_sec=3.5):
    """Sleep for a random time — mimics human browsing speed."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

# ── scrapers ──────────────────────────────────────────────────────────────────

async def scrape_internshala(page, keyword: str, location: str) -> list[dict]:
    """Scrape job listings from Internshala."""
    jobs = []
    url = f"https://internshala.com/jobs/keywords-{keyword.replace(' ', '-')}"

    print(f"\n[Internshala] Visiting: {url}")

    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)   # let JS render

        cards = await page.query_selector_all(".individual_internship")
        print(f"[Internshala] Found {len(cards)} listings")

        for card in cards[:10]:   # limit to first 10
            try:
                title_el    = await card.query_selector(".job-internship-name")
                company_el  = await card.query_selector(".company-name")
                location_el = await card.query_selector(".location_link, .locations-label")
                stipend_el  = await card.query_selector(".stipend")
                link_el     = await card.query_selector("a.view_detail_button")

                title    = await title_el.inner_text()    if title_el    else "N/A"
                company  = await company_el.inner_text()  if company_el  else "N/A"
                loc      = await location_el.inner_text() if location_el else "N/A"
                stipend  = await stipend_el.inner_text()  if stipend_el  else "N/A"
                href     = await link_el.get_attribute("href") if link_el else ""
                link     = f"https://internshala.com{href}" if href else "N/A"

                jobs.append({
                    "source":   "Internshala",
                    "title":    title.strip(),
                    "company":  company.strip(),
                    "location": loc.strip(),
                    "stipend":  stipend.strip(),
                    "link":     link,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                continue    # skip broken cards

    except Exception as e:
        print(f"[Internshala] Error: {e}")

    return jobs


async def scrape_naukri(page, keyword: str, location: str) -> list[dict]:
    """Scrape job listings from Naukri."""
    jobs = []
    loc_slug = location.replace(" ", "-").lower()
    kw_slug  = keyword.replace(" ", "-").lower()
    url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}"

    print(f"\n[Naukri] Visiting: {url}")

    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        cards = await page.query_selector_all(".srp-jobtuple-wrapper, article.jobTuple")
        print(f"[Naukri] Found {len(cards)} listings")

        for card in cards[:10]:
            try:
                title_el    = await card.query_selector("a.title, .jobTitle")
                company_el  = await card.query_selector("a.comp-name, .companyName")
                location_el = await card.query_selector(".locWdth, .location")
                exp_el      = await card.query_selector(".expwdth, .experience")
                link_el     = await card.query_selector("a.title, a.jobTitle")

                title    = await title_el.inner_text()    if title_el    else "N/A"
                company  = await company_el.inner_text()  if company_el  else "N/A"
                loc      = await location_el.inner_text() if location_el else "N/A"
                exp      = await exp_el.inner_text()      if exp_el      else "N/A"
                link     = await link_el.get_attribute("href") if link_el else "N/A"

                jobs.append({
                    "source":      "Naukri",
                    "title":       title.strip(),
                    "company":     company.strip(),
                    "location":    loc.strip(),
                    "experience":  exp.strip(),
                    "link":        link if link else "N/A",
                    "scraped_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                continue

    except Exception as e:
        print(f"[Naukri] Error: {e}")

    return jobs


async def scrape_shine(page, keyword: str, location: str) -> list[dict]:
    """Scrape job listings from Shine.com."""
    jobs = []
    url = f"https://www.shine.com/job-search/{keyword.replace(' ', '-')}-jobs-in-{location.replace(' ', '-')}"

    print(f"\n[Shine] Visiting: {url}")

    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        cards = await page.query_selector_all(".jobCard, .job-card")
        print(f"[Shine] Found {len(cards)} listings")

        for card in cards[:10]:
            try:
                title_el    = await card.query_selector(".jobTitle, h3 a")
                company_el  = await card.query_selector(".companyName, .company")
                location_el = await card.query_selector(".location, .jobLocation")
                link_el     = await card.query_selector("a")

                title   = await title_el.inner_text()    if title_el    else "N/A"
                company = await company_el.inner_text()  if company_el  else "N/A"
                loc     = await location_el.inner_text() if location_el else "N/A"
                href    = await link_el.get_attribute("href") if link_el else ""
                link    = f"https://www.shine.com{href}" if href and href.startswith("/") else href

                jobs.append({
                    "source":     "Shine",
                    "title":      title.strip(),
                    "company":    company.strip(),
                    "location":   loc.strip(),
                    "link":       link if link else "N/A",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                continue

    except Exception as e:
        print(f"[Shine] Error: {e}")

    return jobs

# ── deduplication ─────────────────────────────────────────────────────────────

def deduplicate(jobs: list[dict]) -> list[dict]:
    """Remove duplicate jobs based on title + company combo."""
    seen = set()
    unique = []
    for job in jobs:
        key = (job["title"].lower(), job["company"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique

# ── save results ──────────────────────────────────────────────────────────────

def save_json(jobs: list[dict]) -> None:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(jobs)} jobs to {OUTPUT_JSON}")


def save_csv(jobs: list[dict]) -> None:
    if not jobs:
        return
    keys = jobs[0].keys()
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(jobs)
    print(f"✅ Saved {len(jobs)} jobs to {OUTPUT_CSV}")

# ── CLI filter ────────────────────────────────────────────────────────────────

def filter_jobs(jobs: list[dict], keyword: str = "", location: str = "", source: str = "") -> list[dict]:
    """Simple filter by keyword, location, or source."""
    results = jobs
    if keyword:
        results = [j for j in results if keyword.lower() in j["title"].lower()]
    if location:
        results = [j for j in results if location.lower() in j["location"].lower()]
    if source:
        results = [j for j in results if source.lower() == j["source"].lower()]
    return results


def print_jobs(jobs: list[dict]) -> None:
    if not jobs:
        print("No jobs found matching your filter.")
        return
    print(f"\n{'─'*70}")
    for i, job in enumerate(jobs, 1):
        print(f"\n#{i} [{job['source']}]")
        print(f"   Title   : {job['title']}")
        print(f"   Company : {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Link    : {job['link']}")
    print(f"\n{'─'*70}")
    print(f"Total: {len(jobs)} job(s)")

# ── main ──────────────────────────────────────────────────────────────────────

async def run_scraper(keyword: str, location: str) -> list[dict]:
    all_jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # each site gets its own page with a random user-agent
        for scraper_fn, site_name in [
            (scrape_internshala, "Internshala"),
            (scrape_naukri,      "Naukri"),
            (scrape_shine,       "Shine"),
        ]:
            ua = random.choice(USER_AGENTS)
            context = await browser.new_context(user_agent=ua)
            page    = await context.new_page()

            print(f"\n{'='*55}")
            print(f"  Scraping {site_name}...")
            print(f"{'='*55}")

            jobs = await scraper_fn(page, keyword, location)
            all_jobs.extend(jobs)
            random_delay()          # polite pause between sites

            await context.close()

        await browser.close()

    # clean up duplicates
    unique_jobs = deduplicate(all_jobs)
    print(f"\n📦 Total collected : {len(all_jobs)}")
    print(f"📦 After dedupe    : {len(unique_jobs)}")
    return unique_jobs


def main():
    print("=" * 55)
    print("  Job Listings Aggregator")
    print("=" * 55)
    print("\n1. Scrape fresh jobs")
    print("2. Filter saved jobs")

    choice = input("\nChoice (1/2): ").strip()

    if choice == "1":
        keyword  = input("Search keyword (e.g. python developer): ").strip() or "python developer"
        location = input("Location (e.g. bangalore): ").strip() or "bangalore"

        jobs = asyncio.run(run_scraper(keyword, location))
        save_json(jobs)
        save_csv(jobs)
        print_jobs(jobs)

    elif choice == "2":
        if not os.path.isfile(OUTPUT_JSON):
            print("No saved data found. Run option 1 first.")
            return

        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        print("\nLeave blank to skip a filter.")
        kw  = input("Filter by title keyword: ").strip()
        loc = input("Filter by location     : ").strip()
        src = input("Filter by source (Internshala / Naukri / Shine): ").strip()

        filtered = filter_jobs(jobs, kw, loc, src)
        print_jobs(filtered)

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
