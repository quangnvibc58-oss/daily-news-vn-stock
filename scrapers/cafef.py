from .base import fetch_rss, fetch_html

# CafeF RSS feeds covering major categories
RSS_FEEDS = [
    "https://cafef.vn/rss/home.rss",
    "https://cafef.vn/rss/thi-truong-chung-khoan.rss",
    "https://cafef.vn/rss/kinh-te-vi-mo.rss",
    "https://cafef.vn/rss/doanh-nghiep.rss",
]


def scrape_cafef():
    articles = []
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            items = fetch_rss(feed_url)
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    item["source"] = "cafef.vn"
                    articles.append(item)
        except Exception:
            pass

    # Fallback to HTML scraping if RSS returns too few items
    if len(articles) < 5:
        try:
            soup = fetch_html("https://cafef.vn/")
            for tag in soup.select("h3 a, h2 a, .title a, .news-title a")[:30]:
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://cafef.vn" + href
                if title and href and href not in seen:
                    seen.add(href)
                    articles.append({"title": title, "url": href, "description": "", "source": "cafef.vn"})
        except Exception:
            pass

    return articles[:30]
