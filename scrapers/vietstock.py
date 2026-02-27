from .base import fetch_rss, fetch_html

RSS_FEEDS = [
    "https://vietstock.vn/rss/chung-khoan.rss",
    "https://vietstock.vn/rss/tai-chinh.rss",
    "https://vietstock.vn/rss/doanh-nghiep.rss",
    "https://vietstock.vn/rss/kinh-te.rss",
]


def scrape_vietstock():
    articles = []
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            items = fetch_rss(feed_url)
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    item["source"] = "vietstock.vn"
                    articles.append(item)
        except Exception:
            pass

    # Fallback: HTML scraping
    if len(articles) < 5:
        try:
            soup = fetch_html("https://vietstock.vn/")
            for tag in soup.select("h2 a, h3 a, .article-title a, .news-title a, .title a")[:30]:
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://vietstock.vn" + href
                if title and len(title) > 15 and href and href not in seen:
                    seen.add(href)
                    articles.append({"title": title, "url": href, "description": "", "source": "vietstock.vn"})
        except Exception:
            pass

    return articles[:30]
