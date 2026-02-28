import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from doc_builder import build_docx

CATEGORY_LABELS = {
    "vi_mo_viet_nam": ("🏛", "Vĩ mô Việt Nam"),
    "thi_truong":     ("📈", "Thị trường"),
    "the_gioi":       ("🌏", "Thế giới"),
    "doanh_nghiep":   ("🏢", "Doanh nghiệp"),
}


def _build_email_body(summary: dict, session: str, date_str: str) -> str:
    """Email body đơn giản, liệt kê tiêu đề – nội dung chi tiết trong file đính kèm."""
    rows = ""
    for key, (icon, label) in CATEGORY_LABELS.items():
        items = summary.get(key, [])
        if not items:
            continue
        titles_html = "".join(
            f"<li style='margin:3px 0; font-size:13px;'>{it.get('title','')}</li>"
            for it in items
        )
        rows += f"""
        <tr>
          <td style="padding:10px 16px; vertical-align:top; width:160px;
                     font-weight:700; font-size:13px; color:#444;">
            {icon} {label}
          </td>
          <td style="padding:10px 16px;">
            <ul style="margin:0; padding-left:18px; color:#333;">
              {titles_html}
            </ul>
          </td>
        </tr>"""

    total = sum(len(summary.get(k, [])) for k in CATEGORY_LABELS)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:640px;margin:20px auto;background:#fff;border-radius:10px;
              overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.1);">

    <div style="background:linear-gradient(135deg,#1a3a6b,#2e86c1);padding:24px 28px;text-align:center;">
      <h1 style="margin:0;color:#fff;font-size:20px;font-weight:800;">
        📰 BẢN TIN TÀI CHÍNH {session.upper()}
      </h1>
      <p style="margin:6px 0 0;color:#afd8f8;font-size:13px;">{date_str} &nbsp;|&nbsp; {total} tin tổng hợp</p>
    </div>

    <div style="padding:18px 24px;">
      <p style="margin:0 0 14px;font-size:13.5px;color:#555;">
        Bản tin đầy đủ với nội dung tóm tắt và điểm chính được đính kèm trong file
        <strong>Word (.docx)</strong>. Vui lòng mở file để đọc chi tiết.
      </p>

      <table style="width:100%;border-collapse:collapse;border:1px solid #e9ecef;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#f8f9fa;">
            <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;font-weight:600;border-bottom:1px solid #e9ecef;">
              CHUYÊN MỤC
            </th>
            <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;font-weight:600;border-bottom:1px solid #e9ecef;">
              CÁC TIN NỔI BẬT
            </th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div style="background:#f8f9fa;padding:14px 24px;text-align:center;border-top:1px solid #e9ecef;">
      <p style="margin:0;font-size:11px;color:#aaa;">
        Tổng hợp tự động từ 24hmoney · cafef · vietstock · baochinhphu<br>
        Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.
      </p>
    </div>
  </div>
</body>
</html>"""


def send_email(summary: dict, session: str = "Chiều"):
    sender    = os.environ.get("EMAIL_SENDER")
    password  = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT", sender)

    if not sender or not password:
        raise ValueError("EMAIL_SENDER và EMAIL_PASSWORD phải được cấu hình.")

    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    file_date = now.strftime("%Y%m%d_%H%M")
    subject = f"📰 Bản tin tài chính {session} – {date_str}"

    # ── Tạo file Word ─────────────────────────────────────────────────────────
    docx_bytes = build_docx(summary, session)
    filename = f"BanTinTaiChinh_{session}_{file_date}.docx"

    # ── Tạo email ─────────────────────────────────────────────────────────────
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = f"Bản tin tài chính <{sender}>"
    msg["To"]      = recipient

    # Body HTML
    html_body = _build_email_body(summary, session, date_str)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Đính kèm file Word
    part = MIMEBase("application", "vnd.openxmlformats-officedocument.wordprocessingml.document")
    part.set_payload(docx_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    # ── Gửi ──────────────────────────────────────────────────────────────────
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient.split(","), msg.as_string())

    print(f"  Email + file '{filename}' đã gửi đến: {recipient}")
