# 📰 Bản tin tài chính cuối ngày

Tự động thu thập tin tức từ 4 nguồn, phân tích bằng AI (Groq) và gửi email tổng hợp lúc **19:00 ICT** mỗi ngày.

## Các nguồn tin
- [24hmoney.vn](https://24hmoney.vn)
- [cafef.vn](https://cafef.vn)
- [vietstock.vn](https://vietstock.vn)
- [baochinhphu.vn](https://baochinhphu.vn)

## Cấu trúc email
| Chuyên mục | Nội dung |
|---|---|
| 🏛️ Vĩ mô Việt Nam | GDP, lạm phát, chính sách tiền tệ, NHNN |
| 📈 Thị trường | VN-Index, HNX, trái phiếu, BĐS |
| 🌏 Thế giới | Fed, USD, giá dầu, thị trường toàn cầu |
| 🏢 Doanh nghiệp | Kết quả kinh doanh, IPO, M&A |

---

## Hướng dẫn cài đặt

### Bước 1: Fork và Clone repository
```bash
# Fork repo về tài khoản GitHub của bạn, rồi clone:
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### Bước 2: Tạo Gmail App Password
1. Vào [Google Account](https://myaccount.google.com) → **Bảo mật**
2. Bật **Xác minh 2 bước** (nếu chưa có)
3. Vào [App Passwords](https://myaccount.google.com/apppasswords)
4. Chọn **Mail** → **Máy tính Windows** → **Tạo**
5. Copy 16 ký tự (dạng `xxxx xxxx xxxx xxxx`)

### Bước 3: Thêm GitHub Secrets
Vào repo GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Thêm 4 secrets sau:

| Secret Name | Giá trị |
|---|---|
| `GROQ_API_KEY` | API key từ [console.groq.com](https://console.groq.com/keys) |
| `EMAIL_SENDER` | Gmail dùng để gửi (vd: `myemail@gmail.com`) |
| `EMAIL_PASSWORD` | App Password 16 ký tự vừa tạo |
| `EMAIL_RECIPIENT` | Email nhận tin (có thể giống EMAIL_SENDER) |

### Bước 4: Kích hoạt GitHub Actions
- Vào tab **Actions** trong repo → Click **"I understand my workflows, go ahead and enable them"**
- Workflow sẽ tự chạy lúc **19:00 ICT (12:00 UTC)** mỗi ngày

### Chạy thủ công để test
- Vào **Actions** → **Bản tin tài chính cuối ngày** → **Run workflow** → **Run workflow**

---

## Chạy local (để test)

```bash
# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# hoặc: venv\Scripts\activate  # Windows

# Cài dependencies
pip install -r requirements.txt

# Cấu hình environment
cp .env.example .env
# Mở .env và điền thông tin thực

# Chạy
python main.py
```

---

## Cấu trúc project
```
├── .github/workflows/daily_news.yml  # GitHub Actions schedule
├── scrapers/
│   ├── __init__.py      # Gọi tất cả scrapers
│   ├── base.py          # Hàm dùng chung (RSS + HTML)
│   ├── cafef.py
│   ├── money24h.py
│   ├── vietstock.py
│   └── baochinhphu.py
├── ai_summarizer.py     # Groq AI phân loại + tóm tắt
├── email_sender.py      # Gmail SMTP + HTML template
├── main.py              # Entry point
├── requirements.txt
├── .env.example
└── .gitignore
```
