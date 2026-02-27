from .base import fetch_rss, fetch_html

RSS_FEEDS = [
    "https://baochinhphu.vn/rss/kinh-te.rss",
    "https://baochinhphu.vn/rss/home.rss",
    "https://baochinhphu.vn/Utilities/RSSDetail.aspx?CID=563",
]


def scrape_baochinhphu():
    articles = []
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            items = fetch_rss(feed_url)
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    item["source"] = "baochinhphu.vn"
                    articles.append(item)
            if articles:
                break
        except Exception:
            pass

    # Fallback: HTML scraping
    if len(articles) < 5:
        try:
            soup = fetch_html("https://baochinhphu.vn/kinh-te.htm")
            for tag in soup.select("h2 a, h3 a, .news-item a, .title a, article a")[:30]:
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://baochinhphu.vn" + href
                if title and len(title) > 15 and href and href not in seen:
                    seen.add(href)
                    articles.append({"title": title, "url": href, "description": "", "source": "baochinhphu.vn"})
        except Exception:
            pass

    return articles[:30]
