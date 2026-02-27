import requests
import feedparser
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 15


def fetch_rss(url):
    """Parse an RSS feed and return list of article dicts."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:30]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()
        # Strip HTML tags from summary
        if summary:
            soup = BeautifulSoup(summary, "html.parser")
            summary = soup.get_text(separator=" ").strip()
        if title and link:
            articles.append({
                "title": title,
                "url": link,
                "description": summary[:300] if summary else "",
            })
    return articles


def fetch_html(url):
    """Fetch HTML page and return BeautifulSoup object."""
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return BeautifulSoup(resp.text, "lxml")
