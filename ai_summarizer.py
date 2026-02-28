import os
import json
import time
from groq import Groq
from scrapers.base import enrich_articles

MODEL = "llama-3.3-70b-versatile"

# Giới hạn để tránh vượt TPM (12K token/phút free tier)
MAX_ARTICLES_TO_SUMMARIZE = 20   # tối đa 20 bài vào bước tóm tắt
CONTENT_MAX_CHARS = 900          # cắt ngắn content mỗi bài
BATCH_SIZE = 8                   # 8 bài/lần gọi AI ≈ 8K-10K tokens
BATCH_DELAY = 22                 # giây chờ giữa các batch (tránh TPM limit)

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài chính và kinh tế Việt Nam, có kinh nghiệm nhiều năm trong lĩnh vực đầu tư chứng khoán.
Luôn trả lời bằng tiếng Việt. Phân tích súc tích, rõ ràng, tập trung vào những gì quan trọng nhất với nhà đầu tư."""

# ─── Prompt bước 1: chọn bài ────────────────────────────────────────────────

SELECT_PROMPT = """Dưới đây là {count} bài báo tài chính/kinh tế thu thập trong ngày:

{articles_text}

Nhiệm vụ: Chọn lọc các bài QUAN TRỌNG NHẤT, phân vào 4 nhóm:
1. vi_mo_viet_nam – Chính sách kinh tế, GDP, lạm phát, NHNN, ngân sách, xuất nhập khẩu
2. thi_truong – VN-Index, HNX, thanh khoản, khối ngoại, trái phiếu, BĐS, ngoại hối
3. the_gioi – Fed, USD, giá dầu, thị trường quốc tế ảnh hưởng đến Việt Nam
4. doanh_nghiep – KQKD, IPO, M&A, phát hành cổ phiếu, thông tin doanh nghiệp cụ thể

Mỗi nhóm chọn TỐI ĐA 5 bài quan trọng nhất. Tổng không quá 20 bài.
Trả về JSON (chỉ JSON, không thêm text):
{{
  "vi_mo_viet_nam": [0, 3, 7],
  "thi_truong": [1, 5, 12],
  "the_gioi": [2, 9],
  "doanh_nghiep": [4, 6, 8]
}}
(Giá trị là INDEX của bài trong danh sách bên trên)"""

# ─── Prompt bước 2: tóm tắt theo batch ───────────────────────────────────────

SUMMARIZE_PROMPT = """Tóm tắt {count} bài báo sau với nội dung đầy đủ:

{articles_text}

Yêu cầu cho MỖI bài:
- title: tiêu đề gốc
- summary: 2-3 câu liền mạch nêu sự kiện + số liệu cụ thể
- key_points: 3-5 bullet points với thông tin quan trọng nhất (con số, tên tổ chức, mức tăng/giảm, quyết định)
- impact: 1 câu tác động với nhà đầu tư
- source: tên nguồn
- url: link bài báo
- category: một trong [vi_mo_viet_nam, thi_truong, the_gioi, doanh_nghiep]

Trả về JSON array (chỉ JSON, không thêm text):
[{{"title":"...","summary":"...","key_points":["..."],"impact":"...","source":"...","url":"...","category":"..."}}]"""


def _call_groq(client, prompt: str, max_tokens: int = 2048) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    content = resp.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content


def _build_article_list(articles: list) -> str:
    lines = []
    for i, art in enumerate(articles):
        lines.append(f"[{i}] [{art['source']}] {art['title']}")
        if art.get("description"):
            lines.append(f"    {art['description'][:180]}")
    return "\n".join(lines)


def _build_enriched_text(articles: list) -> str:
    lines = []
    for i, art in enumerate(articles):
        lines.append(f"=== Bài {i+1} | {art['source']} ===")
        lines.append(f"Tiêu đề: {art['title']}")
        lines.append(f"URL: {art['url']}")
        content = (art.get("full_content") or art.get("description", ""))[:CONTENT_MAX_CHARS]
        lines.append(f"Nội dung: {content}")
        lines.append("")
    return "\n".join(lines)


def summarize_news(articles: list) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=api_key)

    if not articles:
        return _empty_result()

    # ── Bước 1: AI chọn bài quan trọng ──────────────────────────────────────
    articles_subset = articles[:80]
    print(f"  Bước 1: AI chọn bài từ {len(articles_subset)} tin...")

    sel_prompt = SELECT_PROMPT.format(
        count=len(articles_subset),
        articles_text=_build_article_list(articles_subset),
    )
    sel_raw = _call_groq(client, sel_prompt, max_tokens=400)
    selected_indices = json.loads(sel_raw)

    # Tập hợp các bài được chọn, không trùng, tối đa MAX_ARTICLES_TO_SUMMARIZE
    chosen = []
    seen_idx = set()
    for cat, idxs in selected_indices.items():
        for idx in idxs:
            if isinstance(idx, int) and 0 <= idx < len(articles_subset) and idx not in seen_idx:
                seen_idx.add(idx)
                art = dict(articles_subset[idx])
                art["_category_hint"] = cat
                chosen.append(art)
            if len(chosen) >= MAX_ARTICLES_TO_SUMMARIZE:
                break
        if len(chosen) >= MAX_ARTICLES_TO_SUMMARIZE:
            break

    # ── Bước 2: Fetch full content song song ─────────────────────────────────
    print(f"  Bước 2: Fetch full content cho {len(chosen)} bài đã chọn...")
    chosen = enrich_articles(chosen)

    # ── Bước 3: Tóm tắt theo batch (tránh vượt TPM limit) ────────────────────
    print(f"  Bước 3: AI tóm tắt sâu {len(chosen)} bài (batch {BATCH_SIZE})...")
    all_summarized = []
    batches = [chosen[i:i + BATCH_SIZE] for i in range(0, len(chosen), BATCH_SIZE)]

    for b_idx, batch in enumerate(batches):
        if b_idx > 0:
            print(f"    Chờ {BATCH_DELAY}s để tránh rate limit...")
            time.sleep(BATCH_DELAY)

        print(f"    Batch {b_idx+1}/{len(batches)} ({len(batch)} bài)...")
        sum_prompt = SUMMARIZE_PROMPT.format(
            count=len(batch),
            articles_text=_build_enriched_text(batch),
        )
        try:
            sum_raw = _call_groq(client, sum_prompt, max_tokens=3000)
            batch_result = json.loads(sum_raw)
            all_summarized.extend(batch_result)
        except Exception as e:
            print(f"    Batch {b_idx+1} lỗi: {e} — bỏ qua batch này")

    # ── Sắp xếp lại theo category ─────────────────────────────────────────────
    result = _empty_result()
    for item in all_summarized:
        cat = item.get("category", "")
        if cat in result:
            result[cat].append(item)

    # Giới hạn 8 tin / chuyên mục
    for cat in result:
        result[cat] = result[cat][:8]

    return result


def _empty_result():
    return {
        "vi_mo_viet_nam": [],
        "thi_truong": [],
        "the_gioi": [],
        "doanh_nghiep": [],
    }
