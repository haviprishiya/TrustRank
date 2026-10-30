import smtplib
import logging
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def generate_welcome_email_content(recipient_email: str, recipient_name: Optional[str] = None) -> Dict[str, str]:
        display_name = recipient_name.strip() if recipient_name and recipient_name.strip() else recipient_email.split('@')[0]
        
        subject = f"Welcome to TrustRank, {display_name}! 🚀 Your Real-Time Shopping Assistant"
        
        text_content = f"""Hello {display_name},

Welcome to TrustRank! We're thrilled to have you on board.

TrustRank is your intent-first, real-time shopping research and recommendation platform for Indian e-commerce.

What you can do with your TrustRank account:
1. Intent-First Search: Search products naturally in plain English.
2. Dynamic Requirement Wizard: Get customized recommendations tailored to your exact specs (RAM, budget, ingredients, and more).
3. Real-Time Price Comparison: Compare verified live offers across Amazon India, Flipkart, and Croma with prices in ₹ INR.
4. Unbiased TrustRank Scoring: Objective 0-100 quality scores based on specs match, value for money, and verified buyer reviews.
5. Zero-Fabrication Guarantee: No fake catalogs—strictly live, verified listings.

Get started by searching for anything you need on TrustRank: http://localhost:8000 (or your configured domain).

If you have any questions or feedback, simply reply to this email.

Happy shopping!
The TrustRank Team
https://trustrank.ai
"""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: #1e293b;
      background-color: #f8fafc;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 20px auto;
      background: #ffffff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      border: 1px solid #e2e8f0;
    }}
    .header {{
      background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
      padding: 36px 30px;
      text-align: center;
      color: #ffffff;
    }}
    .header h1 {{
      margin: 0;
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .header p {{
      margin: 8px 0 0;
      font-size: 14px;
      opacity: 0.9;
    }}
    .badge {{
      display: inline-block;
      background: rgba(255, 255, 255, 0.2);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 12px;
    }}
    .content {{
      padding: 32px 30px;
    }}
    .greeting {{
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 16px;
    }}
    .feature-box {{
      background: #f1f5f9;
      border-left: 4px solid #4f46e5;
      padding: 16px 20px;
      margin: 20px 0;
      border-radius: 0 12px 12px 0;
    }}
    .feature-item {{
      margin: 12px 0;
      display: flex;
      align-items: flex-start;
    }}
    .feature-icon {{
      background: #4f46e5;
      color: #ffffff;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
      margin-right: 12px;
      flex-shrink: 0;
    }}
    .cta-button {{
      display: inline-block;
      background: #4f46e5;
      color: #ffffff !important;
      text-decoration: none;
      padding: 14px 32px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 15px;
      text-align: center;
      margin: 24px 0;
      box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);
    }}
    .footer {{
      background: #0f172a;
      color: #94a3b8;
      padding: 24px 30px;
      text-align: center;
      font-size: 12px;
    }}
    .footer a {{
      color: #818cf8;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">⚡ Zero-Fabrication Intelligence</div>
      <h1>Welcome to TrustRank!</h1>
      <p>Your Real-Time Shopping Research & Recommendation Engine</p>
    </div>
    
    <div class="content">
      <div class="greeting">Hi {display_name},</div>
      <p>Thank you for creating an account with <strong>TrustRank</strong>! We're excited to help you make smarter, faster, and truly objective purchasing decisions across major Indian marketplaces.</p>
      
      <div class="feature-box">
        <h3 style="margin-top:0; font-size:15px; color:#1e1b4b;">What you can do on TrustRank:</h3>
        <div class="feature-item">
          <div class="feature-icon">1</div>
          <div><strong>Intent-First Search:</strong> Query naturally (e.g., <em>"gaming laptop 16GB RAM under 70k"</em>) without tedious filtering.</div>
        </div>
        <div class="feature-item">
          <div class="feature-icon">2</div>
          <div><strong>Dynamic Questionnaires:</strong> Answer 2-3 tailored questions to pin down your exact performance and budget needs.</div>
        </div>
        <div class="feature-item">
          <div class="feature-icon">3</div>
          <div><strong>Live Cross-Store Comparison:</strong> Compare real-time prices (₹ INR) and stock across Amazon India, Flipkart, and Croma.</div>
        </div>
        <div class="feature-item">
          <div class="feature-icon">4</div>
          <div><strong>Transparent 0-100 Scoring:</strong> See exactly why a product is rated high or low with clear pros, cons, and review analytics.</div>
        </div>
      </div>

      <div style="text-align: center;">
        <a href="http://localhost:8000" class="cta-button">Start Exploring Products &rarr;</a>
      </div>

      <p style="font-size: 13px; color: #64748b;">
        Need assistance or have questions about a recommendation? Just reply to this email—our team is always here to help.
      </p>
    </div>

    <div class="footer">
      <p style="margin: 0 0 8px;"><strong>TrustRank Shopping Intelligence</strong> — Honest shopping research with zero fake data.</p>
      <p style="margin: 0;">Sent to {recipient_email}. You received this email because you registered an account on TrustRank.</p>
    </div>
  </div>
</body>
</html>
"""
        return {
            "subject": subject,
            "text": text_content,
            "html": html_content
        }

    @classmethod
    def send_welcome_email_sync(cls, recipient_email: str, recipient_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends the welcome email synchronously via SMTP.
        If SMTP credentials are not configured, logs the dispatch safely.
        """
        content = cls.generate_welcome_email_content(recipient_email, recipient_name)
        
        smtp_host = settings.SMTP_HOST.strip()
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USERNAME.strip()
        smtp_pass = settings.SMTP_PASSWORD.strip()
        from_email = settings.EMAILS_FROM_EMAIL.strip() or "noreply@trustrank.ai"
        from_name = settings.EMAILS_FROM_NAME.strip() or "TrustRank"

        # Check if SMTP is configured
        if not smtp_host:
            logger.info(
                "SMTP_HOST not configured. Welcome email to %s logged in simulation mode (Subject: %r)",
                recipient_email,
                content["subject"]
            )
            return {
                "status": "simulated",
                "recipient": recipient_email,
                "subject": content["subject"],
                "message": f"Welcome email prepared and simulated for {recipient_email}. (To deliver live emails, configure SMTP_HOST in .env)"
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = content["subject"]
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = recipient_email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()

            part_text = MIMEText(content["text"], "plain", "utf-8")
            part_html = MIMEText(content["html"], "html", "utf-8")
            msg.attach(part_text)
            msg.attach(part_html)

            if settings.SMTP_USE_SSL or smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                if settings.SMTP_USE_TLS:
                    server.starttls()

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            server.sendmail(from_email, [recipient_email], msg.as_string())
            server.quit()

            logger.info("Welcome email successfully sent to %s via SMTP (%s:%d)", recipient_email, smtp_host, smtp_port)
            return {
                "status": "sent",
                "recipient": recipient_email,
                "subject": content["subject"],
                "message": f"Welcome email sent to {recipient_email}"
            }
        except Exception as e:
            logger.error("Failed to send welcome email to %s via SMTP (%s:%d): %s", recipient_email, smtp_host, smtp_port, str(e))
            return {
                "status": "failed",
                "recipient": recipient_email,
                "error": str(e),
                "message": f"Failed to deliver welcome email via SMTP: {str(e)}"
            }

    @classmethod
    async def send_welcome_email(cls, recipient_email: str, recipient_name: Optional[str] = None) -> Dict[str, Any]:
        """Asynchronously dispatches the welcome email in a threadpool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, cls.send_welcome_email_sync, recipient_email, recipient_name)

    @classmethod
    def send_price_drop_email_sync(
        cls,
        recipient_email: str,
        recipient_name: Optional[str],
        product_title: str,
        target_price: float,
        current_price: float,
        marketplace: str,
        product_url: Optional[str]
    ) -> Dict[str, Any]:
        display_name = recipient_name.strip() if recipient_name and recipient_name.strip() else recipient_email.split('@')[0]
        savings = max(0.0, target_price - current_price)
        subject = f"🔔 Price Drop Alert: {product_title[:40]} is now ₹{current_price:,.0f} on {marketplace}!"

        text_content = f"""Hello {display_name},

Great news! The product you've been tracking on TrustRank has dropped below your target price.

Product: {product_title}
Marketplace: {marketplace}
Your Target Price: ₹{target_price:,.2f}
New Verified Price: ₹{current_price:,.2f}

Link to Product: {product_url or 'https://trustrank.ai'}

This verified price was detected by TrustRank's periodic marketplace monitor.

Happy saving!
The TrustRank Team
"""

        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 30px; border: 1px solid #e2e8f0;">
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 24px; border-radius: 12px; color: #fff; text-align: center;">
      <h1 style="margin: 0; font-size: 22px;">🔔 Price Drop Detected!</h1>
      <p style="margin: 6px 0 0; opacity: 0.9;">Your target price has been reached</p>
    </div>
    <div style="padding: 24px 0;">
      <h3 style="color: #0f172a; margin-top: 0;">{product_title}</h3>
      <p style="color: #64748b; font-size: 13px;">Marketplace: <strong>{marketplace}</strong></p>
      <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; padding: 16px; margin: 16px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: #047857; font-size: 14px;">Your Target:</span>
          <strong style="color: #047857; font-size: 15px;">₹{target_price:,.2f}</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #065f46; font-size: 14px;">Current Verified Price:</span>
          <strong style="color: #065f46; font-size: 18px;">₹{current_price:,.2f}</strong>
        </div>
      </div>
      {f'<a href="{product_url}" style="display: inline-block; background: #4f46e5; color: #fff; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 14px; margin-top: 12px;">View on {marketplace}</a>' if product_url else ''}
    </div>
    <div style="border-top: 1px solid #f1f5f9; padding-top: 16px; font-size: 12px; color: #94a3b8; text-align: center;">
      TrustRank Shopping Intelligence • Periodic Price Monitor
    </div>
  </div>
</body>
</html>"""

        content = {"subject": subject, "text": text_content, "html": html_content}
        smtp_host = settings.SMTP_HOST.strip()
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USERNAME.strip()
        smtp_pass = settings.SMTP_PASSWORD.strip()
        from_email = settings.EMAILS_FROM_EMAIL
        from_name = settings.EMAILS_FROM_NAME

        if not smtp_host:
            logger.info("SMTP_HOST not configured. Simulating price drop notification for %s", recipient_email)
            return {"status": "simulated", "recipient": recipient_email, "subject": subject}

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = recipient_email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            if settings.SMTP_USE_SSL or smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                if settings.SMTP_USE_TLS:
                    server.starttls()

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            server.sendmail(from_email, [recipient_email], msg.as_string())
            server.quit()
            logger.info("Price drop alert email sent to %s", recipient_email)
            return {"status": "sent", "recipient": recipient_email, "subject": subject}
        except Exception as e:
            logger.error("Failed to send price drop alert email: %s", str(e))
            return {"status": "failed", "error": str(e)}

    @classmethod
    async def send_price_drop_email(
        cls,
        recipient_email: str,
        recipient_name: Optional[str],
        product_title: str,
        target_price: float,
        current_price: float,
        marketplace: str,
        product_url: Optional[str]
    ) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            cls.send_price_drop_email_sync,
            recipient_email,
            recipient_name,
            product_title,
            target_price,
            current_price,
            marketplace,
            product_url
        )
