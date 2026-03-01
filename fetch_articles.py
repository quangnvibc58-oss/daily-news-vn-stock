#!/usr/bin/env python3
"""
Bước 1 – chạy lúc 09:00 và 17:00 ICT.
Chỉ thu thập tin, lưu ra articles_cache.json để bước 2 dùng.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from scrapers import scrape_all

def main():
    now_ict = datetime.now(timezone(timedelta(hours=7)))
    print(f"[FETCH] {now_ict.strftime('%d/%m/%Y %H:%M')} ICT – Bắt đầu thu thập tin tức...")

    articles = scrape_all()
    print(f"  Tổng cộng: {len(articles)} bài")

    if not articles:
        print("  Không có bài nào. Kết thúc.")
        sys.exit(1)

    with open("articles_cache.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"  Đã lưu {len(articles)} bài vào articles_cache.json")
    print("[FETCH] Hoàn thành.")

if __name__ == "__main__":
    main()
