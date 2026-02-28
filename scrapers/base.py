import requests
import feedparser
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 12

# CSS selectors để tìm phần nội dung chính của bài báo
CONTENT_SELECTORS = [
    "div.article-body",
    "div.content-detail",
    "div.article-content",
    "div#article-body",
    "div.detail-content",
    "div.news-content",
    "div.post-content",
    "div.entry-content",
    "div.article__body",
    "section.article-body",
    "article",
    "div.content",
]


def fetch_rss(url):
    """Parse an RSS feed and return list of article dicts."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:30]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()
        if summary:
            soup = BeautifulSoup(summary, "html.parser")
            summary = soup.get_text(separator=" ").strip()
        if title and link:
            articles.append({
                "title": title,
                "url": link,
                "description": summary[:400] if summary else "",
            })
    return articles


def fetch_html(url):
    """Fetch HTML page and return BeautifulSoup object."""
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return BeautifulSoup(resp.text, "lxml")


def fetch_article_content(url: str, max_chars: int = 2500) -> str:
    """Fetch và extract nội dung chính của bài báo."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Xóa các phần không cần thiết
        for tag in soup(["script", "style", "nav", "header", "footer",
                          "aside", "figure", "iframe", "form", "button",
                          "noscript"]):
            tag.decompose()

        # Thử các selector phổ biến
        content = ""
        for selector in CONTENT_SELECTORS:
            block = soup.select_one(selector)
            if block:
                text = block.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    content = text
                    break

        # Fallback: lấy tất cả thẻ <p>
        if not content:
            paras = soup.find_all("p")
            content = "\n".join(
                p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 40
            )

        # Dọn dẹp khoảng trắng thừa
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        content = "\n".join(lines)
        return content[:max_chars]
    except Exception:
        return ""


def enrich_articles(articles: list, max_workers: int = 10) -> list:
    """Fetch full content cho từng bài báo song song (parallel)."""
    def _fetch(art):
        content = fetch_article_content(art["url"])
        art["full_content"] = content if len(content) > 100 else art.get("description", "")
        return art

    enriched = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch, art): art for art in articles}
        for future in as_completed(futures):
            try:
                enriched.append(future.result())
            except Exception:
                orig = futures[future]
                orig["full_content"] = orig.get("description", "")
                enriched.append(orig)
    return enriched
