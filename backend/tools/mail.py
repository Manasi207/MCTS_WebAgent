#backend/tools/mail.py
import smtplib
import imaplib
import email
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from llm import get_llm

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")

def send_email(recipient, subject, body):
    """Send email using configured SMTP settings"""
    
    if not SMTP_USER or not SMTP_PASS:
        return "⚠️ SMTP credentials not configured in .env file"
    
    try:
        # Send email exactly as user typed (no LLM modification)
        msg = EmailMessage()
        msg["From"] = EMAIL_FROM or SMTP_USER
        msg["To"] = recipient
        msg["Subject"] = subject or "No Subject"
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)

        return "✅ Email sent successfully"
    
    except Exception as e:
        return f"❌ Error sending email: {str(e)}"


def fetch_unread_emails():
    """Fetch 5 most recent emails from inbox"""
    
    if not SMTP_USER or not SMTP_PASS:
        return "⚠️ Email credentials not configured in .env file"
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(SMTP_USER, SMTP_PASS)
        mail.select("inbox")

        # Search for ALL emails (not just unread)
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()

        if not email_ids:
            return "📭 No emails found in inbox"

        # Get last 5 emails (most recent)
        recent_ids = email_ids[-5:]
        summaries = []
        
        for eid in recent_ids:
            try:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract email body (first 150 chars only for speed)
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()[:150]
                            except:
                                body = "Unable to decode"
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()[:150]
                    except:
                        body = "Unable to decode"
                
                summaries.append({
                    "from": msg["From"],
                    "subject": msg["Subject"],
                    "date": msg["Date"],
                    "preview": body
                })
            except Exception as e:
                continue

        mail.close()
        mail.logout()

        if not summaries:
            return "❌ Could not fetch emails"

        # Simple summary without LLM for speed
        result = f"📧 Latest {len(summaries)} emails:\n\n"
        for i, e in enumerate(summaries, 1):
            result += f"{i}. From: {e['from']}\n"
            result += f"   Subject: {e['subject']}\n"
            result += f"   Date: {e['date']}\n"
            result += f"   Preview: {e['preview']}...\n\n"

        return result
    
    except Exception as e:
        return f"❌ Error fetching emails: {str(e)}"

