#!/usr/bin/env python3
"""
Chạy thủ công: fetch + AI tóm tắt + gửi mail trong một lần.
Dùng để test local hoặc chạy ad-hoc.
Trong production, hãy dùng 2 workflow riêng:
  - fetch_news.yml  → python fetch_articles.py
  - send_news.yml   → python summarize_and_send.py
"""
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from scrapers import scrape_all
from ai_summarizer import summarize_news
from email_sender import send_email


def get_session() -> str:
    utc_hour = datetime.now(timezone.utc).hour
    return "Sáng" if utc_hour < 8 else "Chiều"


def main():
    session = get_session()
    now_ict = datetime.now(timezone(timedelta(hours=7)))

    print("=" * 55)
    print(f"  BẢN TIN TÀI CHÍNH {session.upper()} – {now_ict.strftime('%d/%m/%Y %H:%M')} ICT")
    print("  (Chế độ: fetch + AI + gửi mail trong một lần)")
    print("=" * 55)

    print("\n[1/3] Thu thập tin tức từ các nguồn...")
    articles = scrape_all()
    print(f"  Tổng cộng: {len(articles)} bài")

    if not articles:
        print("  Không có bài nào. Kết thúc.")
        sys.exit(1)

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

    print(f"\n[3/3] Tạo file Word và gửi email ({session})...")
    send_email(summary, session=session)

    print("\n✓ Hoàn thành!")
    print("=" * 55)


if __name__ == "__main__":
    main()
