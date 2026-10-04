import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM_NAME,
    SMTP_FROM_EMAIL,
)


def send_otp_email(
    recipient_email: str,
    otp: str,
) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USER / DEFAULT_FROM_EMAIL or SMTP_PASSWORD / EMAIL_HOST_PASSWORD is not configured in .env."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "ResearchMate Email Verification"
    from_address = SMTP_FROM_EMAIL or SMTP_USER
    msg["From"] = f"{SMTP_FROM_NAME} <{from_address}>"
    msg["To"] = recipient_email

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 24px; border: 1px solid #e5e5e5; border-radius: 12px; background-color: #ffffff;">
        <h2 style="color: #202123; margin-top: 0;">Verify your ResearchMate account</h2>
        
        <p style="color: #555555; font-size: 15px; line-height: 1.5;">
            Your verification code is:
        </p>

        <div style="background-color: #f7f7f8; padding: 16px; text-align: center; border-radius: 8px; font-size: 30px; font-weight: bold; letter-spacing: 8px; color: #111111; margin: 20px 0;">
            {otp}
        </div>

        <p style="color: #666666; font-size: 14px; line-height: 1.5;">
            This code will expire in 10 minutes.
        </p>

        <p style="color: #888888; font-size: 13px; line-height: 1.5; margin-top: 24px; border-top: 1px solid #eee; padding-top: 16px;">
            If you did not create a ResearchMate account, you can safely ignore this email.
        </p>

        <p style="color: #555555; font-size: 14px; margin-bottom: 0;">
            Regards,<br>
            <strong>ResearchMate Team</strong>
        </p>
    </div>
    """

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(from_address, [recipient_email], msg.as_string())
    except Exception as e:
        raise RuntimeError(f"Failed to send email via Gmail SMTP: {str(e)}")