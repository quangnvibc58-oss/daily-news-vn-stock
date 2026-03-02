"""
Quản lý lịch sử bài báo đã gửi, lưu trong sent_history.json.
- Lọc trùng theo URL (chính xác) và tiêu đề (độ tương đồng ≥ 70%)
- Tự xóa bài cũ hơn 30 ngày
- Commit và push file lên GitHub sau mỗi lần gửi
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta

HISTORY_FILE = "sent_history.json"
KEEP_DAYS = 30               # Giữ lịch sử 30 ngày
SIMILARITY_THRESHOLD = 0.70  # Jaccard ≥ 70% → coi là trùng tiêu đề

# Stopwords tiếng Việt và tiếng Anh phổ biến (bỏ khi so sánh tiêu đề)
STOP_WORDS = {
    "và", "của", "cho", "với", "trong", "là", "có", "được", "các", "một",
    "này", "đã", "sẽ", "về", "tại", "từ", "theo", "đến", "trên", "khi",
    "sau", "hay", "hoặc", "vào", "ra", "đi", "lên", "xuống", "bị", "do",
    "the", "a", "an", "in", "of", "to", "is", "are", "at", "by", "for",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> set:
    """Chuẩn hóa và tách từ, loại stop words."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return {w for w in text.split() if w and w not in STOP_WORDS}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ─── Load / Save ─────────────────────────────────────────────────────────────

def load_history() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {"entries": [], "total_sent": 0}
    with open(HISTORY_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_history(history: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ─── Core logic ──────────────────────────────────────────────────────────────

def filter_new_articles(articles: list) -> tuple:
    """
    Lọc ra các bài CHƯA gửi bao giờ.
    Trả về (bài_mới, số_bài_bị_loại).
    """
    history = load_history()
    entries = history.get("entries", [])

    sent_urls = {e["url"] for e in entries if e.get("url")}
    sent_tokens = [(_tokenize(e["title"]), e["title"]) for e in entries if e.get("title")]

    new_articles, removed = [], 0

    for art in articles:
        url   = art.get("url", "")
        title = art.get("title", "")

        # 1. Trùng URL chính xác
        if url and url in sent_urls:
            removed += 1
            continue

        # 2. Tiêu đề quá tương đồng (có thể cùng tin, khác nguồn / đường link)
        art_tokens = _tokenize(title)
        is_dup = any(
            _jaccard(art_tokens, st) >= SIMILARITY_THRESHOLD
            for st, _ in sent_tokens
        )
        if is_dup:
            removed += 1
            continue

        new_articles.append(art)

    return new_articles, removed


def record_sent(summary: dict, session: str):
    """
    Lưu các bài vừa gửi vào lịch sử.
    Gọi SAU khi email đã gửi thành công.
    """
    history = load_history()
    entries = history.get("entries", [])

    now = datetime.now(timezone(timedelta(hours=7)))
    date_str  = now.strftime("%Y-%m-%d")
    ts_str    = now.strftime("%Y-%m-%dT%H:%M")

    added = 0
    for category, items in summary.items():
        for item in items:
            url   = item.get("url", "")
            title = item.get("title", "")
            if url and title:
                entries.append({
                    "url":        url,
                    "title":      title,
                    "category":   category,
                    "date_sent":  date_str,
                    "sent_at":    ts_str,
                    "session":    session,
                })
                added += 1

    # Xóa bài cũ hơn KEEP_DAYS ngày
    cutoff = (datetime.now() - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    entries = [e for e in entries if e.get("date_sent", "9999") >= cutoff]

    history["entries"]      = entries
    history["total_sent"]   = len(entries)
    history["last_updated"] = ts_str

    _save_history(history)
    print(f"  Đã lưu {added} bài mới vào {HISTORY_FILE} (tổng: {len(entries)} bài / {KEEP_DAYS} ngày)")


def push_history():
    """
    Commit và push sent_history.json lên GitHub.
    Chạy trong GitHub Actions (có GITHUB_TOKEN tự động).
    """
    try:
        subprocess.run(
            ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
            check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "github-actions[bot]"],
            check=True, capture_output=True
        )
        subprocess.run(["git", "add", HISTORY_FILE], check=True, capture_output=True)

        # Kiểm tra có thay đổi không
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], capture_output=True
        )
        if diff.returncode == 0:
            print("  sent_history.json không đổi, bỏ qua commit.")
            return

        subprocess.run(
            ["git", "commit", "-m", f"chore: update sent history [skip ci]"],
            check=True, capture_output=True
        )
        subprocess.run(["git", "push"], check=True, capture_output=True)
        print(f"  Đã push {HISTORY_FILE} lên GitHub.")
    except subprocess.CalledProcessError as e:
        # Không để lỗi lịch sử làm hỏng cả workflow
        print(f"  Cảnh báo: không push được history ({e})")


def print_stats():
    """In thống kê lịch sử để debug."""
    history = load_history()
    entries = history.get("entries", [])
    if not entries:
        print("  (Chưa có lịch sử nào)")
        return
    by_date = {}
    for e in entries:
        d = e.get("date_sent", "?")
        by_date[d] = by_date.get(d, 0) + 1
    print(f"  Lịch sử: {len(entries)} bài trong {KEEP_DAYS} ngày qua")
    for d in sorted(by_date, reverse=True)[:7]:
        print(f"    {d}: {by_date[d]} bài")
