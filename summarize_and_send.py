#!/usr/bin/env python3
"""
Bước 2 – chạy lúc 11:00 và 19:00 ICT.
Đọc articles_cache.json (đã fetch từ 2 tiếng trước), chạy AI tóm tắt, gửi mail.
"""
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from cache_manager import download_cache
from scrapers import scrape_all
from ai_summarizer import summarize_news
from email_sender import send_email


def get_session() -> tuple[str, str]:
    """Trả về (session_label, artifact_name) dựa theo giờ UTC."""
    utc_hour = datetime.now(timezone.utc).hour
    if utc_hour < 8:
        return "Sáng", "articles-morning"
    else:
        return "Chiều", "articles-evening"


def load_articles() -> list:
    """Ưu tiên đọc cache, fallback sang fetch trực tiếp."""
    session, artifact_name = get_session()

    # 1. Thử tải từ GitHub Artifact (được fetch từ 2h trước)
    print(f"  Tải cache '{artifact_name}' từ workflow fetch_news...")
    if download_cache(artifact_name):
        with open("articles_cache.json", encoding="utf-8") as f:
            return json.load(f)

    # 2. Kiểm tra file cache local (chạy thủ công / test local)
    if os.path.exists("articles_cache.json"):
        print("  Dùng articles_cache.json có sẵn ở local.")
        with open("articles_cache.json", encoding="utf-8") as f:
            return json.load(f)

    # 3. Fallback: fetch trực tiếp ngay lúc này
    print("  Không có cache – fetch trực tiếp (fallback)...")
    return scrape_all()


def main():
    session, _ = get_session()
    now_ict = datetime.now(timezone(timedelta(hours=7)))

    print("=" * 55)
    print(f"  BẢN TIN TÀI CHÍNH {session.upper()} – {now_ict.strftime('%d/%m/%Y %H:%M')} ICT")
    print("=" * 55)

    # 1. Tải dữ liệu tin tức (từ cache hoặc fetch trực tiếp)
    print("\n[1/3] Tải dữ liệu tin tức...")
    articles = load_articles()
    print(f"  Tổng cộng: {len(articles)} bài")

    if not articles:
        print("  Không có bài nào. Kết thúc.")
        sys.exit(1)

    # 2. Phân tích và tóm tắt bằng AI
    print("\n[2/3] Phân tích và tóm tắt bằng Groq AI...")
    summary = summarize_news(articles)

    total = sum(len(v) for v in summary.values())
    labels = {
        "vi_mo_viet_nam": "Vĩ mô Việt Nam",
        "thi_truong":     "Thị trường",
        "the_gioi":       "Thế giới",
        "doanh_nghiep":   "Doanh nghiệp",
    }
    print(f"  Đã chọn {total} tin nổi bật:")
    for key, items in summary.items():
        print(f"    - {labels[key]}: {len(items)} tin")

    # 3. Tạo file Word + Gửi email
    print(f"\n[3/3] Tạo file Word và gửi email ({session})...")
    send_email(summary, session=session)

    print("\n✓ Hoàn thành!")
    print("=" * 55)


if __name__ == "__main__":
    main()
