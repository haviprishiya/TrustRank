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
        marketplace: str = "Amazon India",
        product_url: Optional[str] = None,
        previous_price: Optional[float] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an authentic HTML price drop alert email via configured SMTP.
        Does not fabricate success when SMTP is unconfigured or fails.
        """
        display_name = recipient_name.strip() if recipient_name and recipient_name.strip() else recipient_email.split('@')[0]
        ref_price = previous_price if previous_price and previous_price > current_price else target_price
        actual_savings = max(0.0, ref_price - current_price)
        subject = f"TrustRank Price Alert: Your Target Price Has Been Reached!"

        text_content = f"""Hello {display_name},

Great news! The product you have been tracking on TrustRank has reached or dropped below your target price.

Product Details:
---------------------------------------------
Product: {product_title}
Marketplace: {marketplace}
Previous / Reference Price: ₹{ref_price:,.2f}
Your Target Price: ₹{target_price:,.2f}
Current Verified Price: ₹{current_price:,.2f}
Your Actual Savings: ₹{actual_savings:,.2f}

View & Buy on {marketplace}:
{product_url or 'https://trustrank.ai'}

This verified price was confirmed by TrustRank's automated marketplace monitoring engine.
No fake discounts or outdated prices.

Happy shopping!
The TrustRank Team
https://trustrank.ai
"""

        prev_price_html = f"""
          <div style="text-align: center; padding: 10px; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold;">Previous Price</div>
            <div style="font-size: 14px; color: #94a3b8; text-decoration: line-through; margin-top: 4px;">₹{ref_price:,.0f}</div>
          </div>
        """ if ref_price > current_price else ""

        savings_badge_html = f"""
          <div style="display: inline-block; background: #ecfdf5; border: 1px solid #10b981; color: #047857; font-weight: bold; font-size: 13px; padding: 6px 14px; border-radius: 20px; margin-top: 12px;">
            🎉 You save ₹{actual_savings:,.0f}!
          </div>
        """ if actual_savings > 0 else ""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #0f172a;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 18px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 32px 24px; text-align: center; border-bottom: 4px solid #10b981;">
      <div style="display: inline-block; background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; padding: 4px 12px; border-radius: 9999px; margin-bottom: 8px;">
        TrustRank Price Alert
      </div>
      <h1 style="margin: 0; font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">
        🔔 Target Price Reached!
      </h1>
      <p style="margin: 6px 0 0; color: #94a3b8; font-size: 13px;">
        Verified price drop confirmed on {marketplace}
      </p>
    </div>

    <!-- Body -->
    <div style="padding: 28px 24px;">
      <p style="margin: 0 0 16px; font-size: 15px; color: #334155;">
        Hello <strong>{display_name}</strong>,
      </p>
      <p style="margin: 0 0 20px; font-size: 14px; color: #475569; line-height: 1.6;">
        Great news! The product you've been tracking has reached or fallen below your desired price threshold.
      </p>

      <!-- Product Card -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; margin-bottom: 24px;">
        <div style="display: inline-block; background: #e0e7ff; color: #4338ca; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; margin-bottom: 8px;">
          {marketplace}
        </div>
        <h2 style="margin: 0 0 16px; font-size: 16px; font-weight: 700; color: #0f172a; line-height: 1.4;">
          {product_title}
        </h2>

        <!-- Price Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin: 16px 0;">
          {prev_price_html}
          <div style="text-align: center; padding: 10px; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold;">Your Target</div>
            <div style="font-size: 15px; color: #4f46e5; font-weight: bold; margin-top: 4px;">₹{target_price:,.0f}</div>
          </div>
          <div style="text-align: center; padding: 10px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px;">
            <div style="font-size: 11px; color: #065f46; text-transform: uppercase; font-weight: bold;">Current Verified</div>
            <div style="font-size: 18px; color: #047857; font-weight: 900; margin-top: 2px;">₹{current_price:,.0f}</div>
          </div>
        </div>

        <div style="text-align: center;">
          {savings_badge_html}
        </div>
      </div>

      <!-- Action Button -->
      {f'''
      <div style="text-align: center; margin: 28px 0 16px;">
        <a href="{product_url}" style="display: inline-block; background: #4f46e5; color: #ffffff; text-decoration: none; font-weight: 700; font-size: 14px; padding: 14px 28px; border-radius: 12px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);">
          Claim Deal on {marketplace} &rarr;
        </a>
      </div>
      ''' if product_url else ''}

      <p style="margin: 20px 0 0; font-size: 12px; color: #94a3b8; text-align: center; line-height: 1.5;">
        This alert was sent automatically because the price was verified by TrustRank's background price monitor.
      </p>
    </div>

    <!-- Footer -->
    <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; text-align: center; font-size: 11px; color: #94a3b8;">
      TrustRank Shopping Intelligence &bull; Real-Time Verified Marketplace Analytics<br>
      To manage your alert thresholds, visit your TrustRank Customer Profile dashboard.
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
            logger.warning(
                "SMTP credentials not configured (SMTP_HOST is empty). Price drop email skipped for %s. Set SMTP_HOST in .env to enable live email delivery.",
                recipient_email
            )
            return {
                "status": "not_configured",
                "recipient": recipient_email,
                "subject": subject,
                "message": "SMTP credentials not configured in backend environment."
            }

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
            logger.info("Price drop alert email successfully sent to %s via SMTP (%s:%d)", recipient_email, smtp_host, smtp_port)
            return {"status": "sent", "recipient": recipient_email, "subject": subject, "message": f"Price drop alert sent to {recipient_email}"}
        except Exception as e:
            logger.error("Failed to send price drop alert email to %s via SMTP (%s:%d): %s", recipient_email, smtp_host, smtp_port, str(e))
            return {"status": "failed", "recipient": recipient_email, "error": str(e), "message": f"SMTP delivery failed: {str(e)}"}

    @classmethod
    async def send_price_drop_email(
        cls,
        recipient_email: str,
        recipient_name: Optional[str],
        product_title: str,
        target_price: float,
        current_price: float,
        marketplace: str = "Amazon India",
        product_url: Optional[str] = None,
        previous_price: Optional[float] = None,
        image_url: Optional[str] = None
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
            product_url,
            previous_price,
            image_url
        )
