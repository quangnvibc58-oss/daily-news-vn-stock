import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CATEGORY_CONFIG = {
    "vi_mo_viet_nam": {
        "label": "Vĩ mô Việt Nam",
        "icon": "🏛️",
        "color": "#1a5276",
        "bg": "#d6eaf8",
    },
    "thi_truong": {
        "label": "Thị trường",
        "icon": "📈",
        "color": "#1e8449",
        "bg": "#d5f5e3",
    },
    "the_gioi": {
        "label": "Thế giới",
        "icon": "🌏",
        "color": "#784212",
        "bg": "#fdebd0",
    },
    "doanh_nghiep": {
        "label": "Tin nổi bật từ doanh nghiệp",
        "icon": "🏢",
        "color": "#512e5f",
        "bg": "#f5eef8",
    },
}


def build_html(summary: dict, date_str: str) -> str:
    sections_html = ""
    for key, cfg in CATEGORY_CONFIG.items():
        items = summary.get(key, [])
        if not items:
            continue

        items_html = ""
        for idx, item in enumerate(items, 1):
            title = item.get("title", "")
            s = item.get("summary", "")
            source = item.get("source", "")
            url = item.get("url", "#")
            items_html += f"""
            <div style="margin-bottom:16px; padding:12px 16px; background:#fff;
                        border-left:4px solid {cfg['color']}; border-radius:4px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.07);">
              <div style="font-size:13px; color:#888; margin-bottom:4px;">
                {idx}. <span style="font-weight:600; color:{cfg['color']};">{source}</span>
              </div>
              <a href="{url}" style="font-size:15px; font-weight:700; color:#222;
                 text-decoration:none; line-height:1.4; display:block; margin-bottom:6px;">
                {title}
              </a>
              <p style="margin:0; font-size:13.5px; color:#555; line-height:1.6;">{s}</p>
              <a href="{url}" style="font-size:12px; color:{cfg['color']}; margin-top:6px;
                 display:inline-block; text-decoration:none;">Đọc thêm →</a>
            </div>"""

        sections_html += f"""
        <div style="margin-bottom:32px;">
          <div style="background:{cfg['bg']}; border-radius:8px; padding:10px 18px;
                      margin-bottom:14px; display:flex; align-items:center;">
            <span style="font-size:22px; margin-right:10px;">{cfg['icon']}</span>
            <h2 style="margin:0; font-size:18px; color:{cfg['color']}; font-weight:800;">
              {cfg['label']}
            </h2>
          </div>
          {items_html}
        </div>"""

    total = sum(len(summary.get(k, [])) for k in CATEGORY_CONFIG)

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bản tin tài chính {date_str}</title>
</head>
<body style="margin:0; padding:0; background:#f0f2f5; font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:700px; margin:24px auto; background:#fff; border-radius:12px;
              overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,0.1);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a3a6b 0%,#2e86c1 100%);
                padding:28px 32px; text-align:center;">
      <div style="font-size:28px; margin-bottom:6px;">📰</div>
      <h1 style="margin:0; color:#fff; font-size:22px; font-weight:800; letter-spacing:0.5px;">
        BẢN TIN TÀI CHÍNH CUỐI NGÀY
      </h1>
      <p style="margin:8px 0 0; color:#afd8f8; font-size:14px;">{date_str} | {total} tin tổng hợp</p>
    </div>

    <!-- Content -->
    <div style="padding:28px 32px;">
      {sections_html}
    </div>

    <!-- Footer -->
    <div style="background:#f8f9fa; padding:16px 32px; text-align:center;
                border-top:1px solid #e9ecef;">
      <p style="margin:0; font-size:12px; color:#aaa; line-height:1.6;">
        Bản tin được tổng hợp tự động bởi AI từ các nguồn:
        24hmoney.vn · cafef.vn · vietstock.vn · baochinhphu.vn<br>
        Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.
      </p>
    </div>
  </div>
</body>
</html>"""


def send_email(summary: dict):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT", sender)

    if not sender or not password:
        raise ValueError("EMAIL_SENDER và EMAIL_PASSWORD phải được cấu hình.")

    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    subject = f"📰 Bản tin tài chính cuối ngày – {date_str}"

    html_body = build_html(summary, date_str)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Bản tin tài chính <{sender}>"
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient.split(","), msg.as_string())

    print(f"  Email đã gửi đến: {recipient}")
