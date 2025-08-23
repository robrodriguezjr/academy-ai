# academy_site_scraper.py

"""
This script crawls your Academy blog index page,
extracts all blog post links, visits each one, extracts content + embedded videos,
and saves Markdown versions for Obsidian and/or Airtable.

Dependencies:
    pip install playwright beautifulsoup4 markdownify requests
    playwright install
"""

import os
import re
import json
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urljoin, urlparse
from pathlib import Path
from playwright.sync_api import sync_playwright

# --- Config ---
BLOG_INDEX_URL = "https://creativepathworkshops.com/blog"
BLOG_MATCH_PATTERN = "/blog/"

OUTPUT_DIR = Path("./academy_scrape")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Optional: Obsidian vault path
OBSIDIAN_VAULT_PATH = Path("/Users/robjr/Documents/RR Main Vault/Academy Blog")
OBSIDIAN_VAULT_PATH.mkdir(parents=True, exist_ok=True)

# Optional: Airtable settings
USE_AIRTABLE = False  # Set to True and configure below to enable
AIRTABLE_BASE_ID = "your_base_id"
AIRTABLE_API_KEY = "your_api_key"
AIRTABLE_TABLE_NAME = "Academy Blog Posts"

# --- Utilities ---
def slugify(text):
    return re.sub(r'\W+', '-', text.lower()).strip('-')

def extract_video_links(soup):
    links = []
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if any(domain in src for domain in ["youtube.com", "wistia", "bunny"]):
            links.append(src)
    return links

def push_to_airtable(record):
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    data = {"fields": record}
    response = requests.post(url, headers=headers, json=data)
    return response.status_code, response.text

def extract_blog_post_urls(start_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(start_url)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        base = start_url.split("/")[0] + "//" + start_url.split("/")[2]
        urls = set()
        main_section = soup.find("main") or soup.body
        for a in main_section.select(".fl-post-feed-title a[href]"):
            href = a["href"]
            href = a["href"]
            full_url = urljoin(base, href)
        full_url = urljoin(base, href)
        path = urlparse(full_url).path
        # Include root-level posts only (e.g. /post-slug/)
        if all(x not in path for x in ["/tag/", "/category/", "/page/", "/live-session/"]):
                urls.add(full_url)

        browser.close()
        return sorted(urls)

# --- Main ---
# Step 1: Extract all individual blog post links from the archive page
blog_urls = extract_blog_post_urls(BLOG_INDEX_URL)
print(f"Found {len(blog_urls)} blog posts.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for url in blog_urls:
        print(f"Scraping: {url}")
        page.goto(url)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string.strip() if soup.title else urlparse(url).path.strip("/").replace("/", " ")
        slug = slugify(title)
        main = soup.find("main") or soup.body
        video_links = extract_video_links(soup)
        markdown = md(str(main))

        # Prepare output
        header = f"# {title}\n\n"
        videos_md = "\n".join(f"- Video: {link}" for link in video_links)
        full_md = f"{header}{videos_md}\n\n---\n\n{markdown}"

        # Write to local .md file
        output_path = OUTPUT_DIR / f"{slug}.md"
        with open(output_path, "w") as f:
            f.write(full_md)

        # Optionally write to Obsidian
        if OBSIDIAN_VAULT_PATH:
            obsidian_path = OBSIDIAN_VAULT_PATH / f"{slug}.md"
            with open(obsidian_path, "w") as f:
                f.write(full_md)

        # Optionally push to Airtable
        if USE_AIRTABLE:
            record = {
                "Title": title,
                "URL": url,
                "Video Links": ", ".join(video_links),
                "Markdown": markdown[:5000]  # Airtable text limits
            }
            status, msg = push_to_airtable(record)
            print(f"Airtable response: {status} - {msg}")

    browser.close()

print("✅ Finished crawling blog index and exporting.")
