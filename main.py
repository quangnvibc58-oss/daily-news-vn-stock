#!/usr/bin/env python3
"""
Bản tin tài chính – News Aggregator
Chạy 2 lần/ngày: 11:00 ICT (sáng) và 19:00 ICT (chiều)
"""
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from scrapers import scrape_all
from ai_summarizer import summarize_news
from email_sender import send_email


def get_session() -> str:
    """Xác định bản tin Sáng hay Chiều dựa theo giờ UTC hiện tại."""
    utc_hour = datetime.now(timezone.utc).hour
    # 04:00 UTC = 11:00 ICT → Bản tin Sáng
    # 12:00 UTC = 19:00 ICT → Bản tin Chiều
    return "Sáng" if utc_hour < 8 else "Chiều"


def main():
    session = get_session()
    now_ict = datetime.now(timezone(timedelta(hours=7)))

    print("=" * 55)
    print(f"  BẢN TIN TÀI CHÍNH {session.upper()} – {now_ict.strftime('%d/%m/%Y %H:%M')} ICT")
    print("=" * 55)

    # 1. Thu thập tin tức
    print("\n[1/3] Thu thập tin tức từ các nguồn...")
    articles = scrape_all()
    print(f"  Tổng cộng: {len(articles)} bài")

    if len(articles) == 0:
        print("  Không có bài nào được thu thập. Kết thúc.")
        sys.exit(1)

    # 2. Phân tích và tóm tắt bằng AI
    print("\n[2/3] Phân tích và tóm tắt bằng Groq AI...")
    summary = summarize_news(articles)

    total_selected = sum(len(v) for v in summary.values())
    print(f"  Đã chọn {total_selected} tin nổi bật:")
    labels = {
        "vi_mo_viet_nam": "Vĩ mô Việt Nam",
        "thi_truong":     "Thị trường",
        "the_gioi":       "Thế giới",
        "doanh_nghiep":   "Doanh nghiệp",
    }
    for key, items in summary.items():
        print(f"    - {labels.get(key, key)}: {len(items)} tin")

    # 3. Tạo file Word + Gửi email
    print(f"\n[3/3] Tạo file Word và gửi email ({session})...")
    send_email(summary, session=session)

    print("\n✓ Hoàn thành!")
    print("=" * 55)


if __name__ == "__main__":
    main()
