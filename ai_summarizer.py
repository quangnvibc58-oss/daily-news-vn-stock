import os
import json
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài chính và kinh tế Việt Nam.
Nhiệm vụ của bạn là phân loại và tóm tắt tin tức tài chính/kinh tế theo 4 nhóm.
Luôn trả lời bằng tiếng Việt, ngắn gọn, súc tích và chính xác."""

USER_PROMPT_TEMPLATE = """Dưới đây là danh sách các tin tức tài chính/kinh tế thu thập trong ngày.

{articles_text}

---

Hãy phân loại và chọn lọc các tin nổi bật nhất, chia thành 4 nhóm sau:

1. **Vĩ mô Việt Nam** – Các tin về chính sách kinh tế, GDP, lạm phát, tiền tệ, ngân hàng nhà nước, chính phủ, xuất nhập khẩu.
2. **Thị trường** – Tin về thị trường chứng khoán (VN-Index, HNX), trái phiếu, bất động sản, hàng hóa, ngoại hối.
3. **Thế giới** – Tin kinh tế/tài chính quốc tế ảnh hưởng đến Việt Nam, Fed, USD, giá dầu, thị trường toàn cầu.
4. **Tin nổi bật từ doanh nghiệp** – Kết quả kinh doanh, IPO, M&A, phát hành cổ phiếu, tin tức doanh nghiệp cụ thể.

Yêu cầu:
- Mỗi nhóm chọn 5-10 tin quan trọng nhất
- Mỗi tin gồm: tiêu đề gốc, 1-2 câu tóm tắt nội dung chính, nguồn và link
- Ưu tiên tin có tác động lớn đến thị trường hoặc nhà đầu tư

Trả về JSON theo đúng format sau (không thêm text bên ngoài JSON):
{{
  "vi_mo_viet_nam": [
    {{"title": "...", "summary": "...", "source": "...", "url": "..."}}
  ],
  "thi_truong": [
    {{"title": "...", "summary": "...", "source": "...", "url": "..."}}
  ],
  "the_gioi": [
    {{"title": "...", "summary": "...", "source": "...", "url": "..."}}
  ],
  "doanh_nghiep": [
    {{"title": "...", "summary": "...", "source": "...", "url": "..."}}
  ]
}}"""


def build_articles_text(articles):
    """Convert article list to formatted text for the prompt."""
    lines = []
    for i, art in enumerate(articles, 1):
        line = f"{i}. [{art['source']}] {art['title']}"
        if art.get("description"):
            line += f"\n   Mô tả: {art['description'][:200]}"
        line += f"\n   Link: {art['url']}"
        lines.append(line)
    return "\n\n".join(lines)


def summarize_news(articles):
    """Use Groq API to categorize and summarize articles."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=api_key)

    if not articles:
        return _empty_result()

    # Limit to 120 articles to stay within token limits
    articles_text = build_articles_text(articles[:120])
    prompt = USER_PROMPT_TEMPLATE.format(articles_text=articles_text)

    print(f"  Gửi {min(len(articles), 120)} bài đến Groq AI để phân tích...")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON from response (in case model adds extra text)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    result = json.loads(content)
    return result


def _empty_result():
    return {
        "vi_mo_viet_nam": [],
        "thi_truong": [],
        "the_gioi": [],
        "doanh_nghiep": [],
    }
