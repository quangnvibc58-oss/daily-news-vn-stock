import os
import json
from groq import Groq
from scrapers.base import enrich_articles

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài chính và kinh tế Việt Nam, có kinh nghiệm nhiều năm trong lĩnh vực đầu tư chứng khoán.
Luôn trả lời bằng tiếng Việt. Phân tích súc tích, rõ ràng, tập trung vào những gì quan trọng nhất với nhà đầu tư."""

# ─── Prompt bước 1: chọn bài ────────────────────────────────────────────────

SELECT_PROMPT = """Dưới đây là {count} bài báo tài chính/kinh tế thu thập trong ngày:

{articles_text}

Nhiệm vụ: Chọn lọc các bài QUAN TRỌNG NHẤT, phân vào 4 nhóm:
1. vi_mo_viet_nam – Chính sách kinh tế, GDP, lạm phát, NHNN, ngân sách, xuất nhập khẩu
2. thi_truong – VN-Index, HNX, thanh khoản, nhà đầu tư nước ngoài, trái phiếu, BĐS, ngoại hối
3. the_gioi – Fed, USD, giá dầu, thị trường quốc tế ảnh hưởng đến Việt Nam
4. doanh_nghiep – KQKD, IPO, M&A, phát hành cổ phiếu, thông tin cụ thể từng doanh nghiệp

Mỗi nhóm chọn 5-8 bài quan trọng nhất. Trả về JSON (chỉ JSON, không thêm text):
{{
  "vi_mo_viet_nam": [0, 3, 7],
  "thi_truong": [1, 5, 12],
  "the_gioi": [2, 9],
  "doanh_nghiep": [4, 6, 8, 11]
}}
(Giá trị là INDEX của bài trong danh sách)"""

# ─── Prompt bước 2: tóm tắt nội dung thật ──────────────────────────────────

SUMMARIZE_PROMPT = """Bạn nhận được {count} bài báo đã có nội dung đầy đủ. Hãy tóm tắt từng bài theo đúng format JSON.

{articles_text}

Yêu cầu cho MỖI bài:
- title: Tiêu đề gốc (giữ nguyên)
- summary: Đoạn tóm tắt 2-3 câu liền mạch, nêu rõ sự kiện + số liệu cụ thể (nếu có)
- key_points: Danh sách 3-5 bullet points với các thông tin quan trọng nhất (con số, tên tổ chức, mức tăng/giảm, thời gian, quyết định cụ thể)
- impact: 1 câu nêu tác động / ý nghĩa với nhà đầu tư
- source: tên nguồn
- url: link bài báo
- category: một trong [vi_mo_viet_nam, thi_truong, the_gioi, doanh_nghiep]

Trả về JSON (chỉ JSON, không thêm text):
[
  {{
    "title": "...",
    "summary": "...",
    "key_points": ["...", "...", "..."],
    "impact": "...",
    "source": "...",
    "url": "...",
    "category": "..."
  }}
]"""


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
    # Strip markdown code fences if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content


def _build_article_list(articles: list) -> str:
    lines = []
    for i, art in enumerate(articles):
        lines.append(f"[{i}] Nguồn: {art['source']}")
        lines.append(f"    Tiêu đề: {art['title']}")
        if art.get("description"):
            lines.append(f"    Tóm tắt RSS: {art['description'][:250]}")
        lines.append(f"    URL: {art['url']}")
        lines.append("")
    return "\n".join(lines)


def _build_enriched_text(articles: list) -> str:
    lines = []
    for i, art in enumerate(articles):
        lines.append(f"=== Bài {i+1} ===")
        lines.append(f"Nguồn: {art['source']} | URL: {art['url']}")
        lines.append(f"Tiêu đề: {art['title']}")
        content = art.get("full_content") or art.get("description", "")
        lines.append(f"Nội dung:\n{content[:2000]}")
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
    articles_subset = articles[:100]
    print(f"  Bước 1: AI chọn bài từ {len(articles_subset)} tin...")

    sel_prompt = SELECT_PROMPT.format(
        count=len(articles_subset),
        articles_text=_build_article_list(articles_subset),
    )
    sel_raw = _call_groq(client, sel_prompt, max_tokens=512)
    selected_indices = json.loads(sel_raw)

    # Tập hợp các bài được chọn (loại trùng)
    chosen = []
    seen_idx = set()
    for cat, idxs in selected_indices.items():
        for idx in idxs:
            if isinstance(idx, int) and 0 <= idx < len(articles_subset) and idx not in seen_idx:
                seen_idx.add(idx)
                art = dict(articles_subset[idx])
                art["_category_hint"] = cat
                chosen.append(art)

    print(f"  Bước 2: Fetch full content cho {len(chosen)} bài đã chọn...")
    chosen = enrich_articles(chosen)

    # ── Bước 2: AI tóm tắt từng bài với nội dung thật ────────────────────────
    print(f"  Bước 3: AI tóm tắt sâu {len(chosen)} bài...")
    sum_prompt = SUMMARIZE_PROMPT.format(
        count=len(chosen),
        articles_text=_build_enriched_text(chosen),
    )
    sum_raw = _call_groq(client, sum_prompt, max_tokens=4096)
    summarized = json.loads(sum_raw)

    # ── Sắp xếp lại theo category ─────────────────────────────────────────────
    result = _empty_result()
    for item in summarized:
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
