from .money24h import scrape_24hmoney
from .cafef import scrape_cafef
from .vietstock import scrape_vietstock
from .baochinhphu import scrape_baochinhphu


def scrape_all():
    """Scrape news from all sources and return combined list."""
    all_news = []
    sources = [
        ("24hmoney.vn", scrape_24hmoney),
        ("cafef.vn", scrape_cafef),
        ("vietstock.vn", scrape_vietstock),
        ("baochinhphu.vn", scrape_baochinhphu),
    ]
    for name, scraper in sources:
        try:
            articles = scraper()
            print(f"  [{name}] Lấy được {len(articles)} bài")
            all_news.extend(articles)
        except Exception as e:
            print(f"  [{name}] Lỗi: {e}")
    return all_news
