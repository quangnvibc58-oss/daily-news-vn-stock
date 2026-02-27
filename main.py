#!/usr/bin/env python3
"""
Bản tin tài chính cuối ngày – News Aggregator
Tự động thu thập, phân tích và gửi email tổng hợp tin tức tài chính.
"""
import sys
from dotenv import load_dotenv

load_dotenv()  # Load .env file if running locally

from scrapers import scrape_all
from ai_summarizer import summarize_news
from email_sender import send_email


def main():
    print("=" * 55)
    print("  BẢN TIN TÀI CHÍNH CUỐI NGÀY – Đang xử lý...")
    print("=" * 55)

    # 1. Thu thập tin tức
    print("\n[1/3] Thu thập tin tức từ các nguồn...")
    articles = scrape_all()
    print(f"  Tổng cộng: {len(articles)} bài")

    if len(articles) == 0:
        print("  Không có bài nào được thu thập. Kết thúc.")
        sys.exit(1)

    # 2. Phân tích và tóm tắt bằng AI
    print("\n[2/3] Phân tích và phân loại bằng Groq AI...")
    summary = summarize_news(articles)

    total_selected = sum(len(v) for v in summary.values())
    print(f"  Đã chọn {total_selected} tin nổi bật:")
    for key, items in summary.items():
        labels = {
            "vi_mo_viet_nam": "Vĩ mô Việt Nam",
            "thi_truong": "Thị trường",
            "the_gioi": "Thế giới",
            "doanh_nghiep": "Doanh nghiệp",
        }
        print(f"    - {labels.get(key, key)}: {len(items)} tin")

    # 3. Gửi email
    print("\n[3/3] Gửi email...")
    send_email(summary)

    print("\n✓ Hoàn thành!")
    print("=" * 55)


if __name__ == "__main__":
    main()
