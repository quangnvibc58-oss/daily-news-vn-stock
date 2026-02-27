from .base import fetch_rss, fetch_html

RSS_FEEDS = [
    "https://24hmoney.vn/rss/home.rss",
    "https://24hmoney.vn/feed",
]


def scrape_24hmoney():
    articles = []
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            items = fetch_rss(feed_url)
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    item["source"] = "24hmoney.vn"
                    articles.append(item)
            if articles:
                break
        except Exception:
            pass

    # Fallback: HTML scraping
    if len(articles) < 5:
        try:
            soup = fetch_html("https://24hmoney.vn/")
            for tag in soup.select("h2 a, h3 a, .article-title a, .news-item a, .title a")[:30]:
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://24hmoney.vn" + href
                if title and len(title) > 15 and href and href not in seen:
                    seen.add(href)
                    articles.append({"title": title, "url": href, "description": "", "source": "24hmoney.vn"})
        except Exception:
            pass

    return articles[:30]
