import smtplib, os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.adk.tools import FunctionTool

logger = logging.getLogger("pointer.emailer")

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USERNAME)

logger.info("📧 Email tool initialized")
logger.info(f"   SMTP_HOST: {SMTP_HOST}")
logger.info(f"   SMTP_PORT: {SMTP_PORT}")
logger.info(f"   SMTP_USERNAME: {'SET' if SMTP_USERNAME else 'NOT SET'}")
logger.info(f"   SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'NOT SET'}")
logger.info(f"   SMTP_FROM: {SMTP_FROM}")


async def send_email(to: str, subject: str, body: str) -> dict:
    """
    Send an email via SMTP.
    
    Args:
        to: Recipient email address (e.g., 'user@example.com')
        subject: Email subject line. If user doesn't specify, use 'Message from Pointer' or create from context.
        body: Email body content - the actual message or selected text to send.
    
    Returns:
        dict: Status with 'status' key ('sent', 'dry_run', or 'error')
    
    Example usage:
        - User says "send this to john@example.com" with selected text:
          send_email(to="john@example.com", subject="Selected Content", body="<the selected text>")
        - User says "email project update to team@company.com":
          send_email(to="team@company.com", subject="Project Update", body="<extract from message or context>")
    """
    print("[DEBUG EMAILER] ========================================")
    print(f"[DEBUG EMAILER] send_email called!")
    print(f"[DEBUG EMAILER] to={to}")
    print(f"[DEBUG EMAILER] subject={subject}")
    print(f"[DEBUG EMAILER] body type={type(body)}")
    print(f"[DEBUG EMAILER] body={body}")
    print("[DEBUG EMAILER] ========================================")
    
    logger.info("=" * 60)
    logger.info("📧 EMAIL TOOL CALLED")
    logger.info("=" * 60)
    logger.info(f"📬 To: {to}")
    logger.info(f"📝 Subject: {subject}")
    logger.info(f"📄 Body type: {type(body)}")
    
    # Ensure body is a string
    if isinstance(body, bytes):
        print("[DEBUG EMAILER] Converting bytes to string")
        body = body.decode('utf-8')
    body = str(body)
    print(f"[DEBUG EMAILER] After conversion, body={body}")
    
    # Remove agent/tool logs that Gemini 2.5 might include
    import re
    original_body = body
    
    # Remove lines containing agent logs
    body = re.sub(r'For context:\[.*?\].*?result:.*?\n?', '', body, flags=re.DOTALL)
    body = re.sub(r'\[.*?_agent\].*?tool.*?\n?', '', body)
    body = re.sub(r'For context:.*?\n?', '', body)
    
    if body != original_body:
        print("[DEBUG EMAILER] Removed agent logs from body")
        logger.info("🧹 Cleaned agent logs from body")
    
    # Clean up markdown code blocks if present
    if '```' in body:
        logger.info("🧹 Cleaning markdown code blocks from body...")
        print("[DEBUG EMAILER] Cleaning markdown code blocks")
        # Remove markdown code fences
        body = re.sub(r'```\w*\n?', '', body)
        print(f"[DEBUG EMAILER] After cleaning, body={body}")
    
    # Clean up extra newlines
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    print(f"[DEBUG EMAILER] Final cleaned body={body}")
    
    logger.info(f"📄 Body length: {len(body)} chars")
    logger.info(f"📄 Body preview: {body[:100]}...")
    
    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD):
        logger.warning("⚠️  SMTP credentials not configured - running in DRY RUN mode")
        print("[DEBUG EMAILER] DRY RUN MODE - SMTP not configured")
        logger.info(f"   Missing: SMTP_HOST={bool(SMTP_HOST)}, USERNAME={bool(SMTP_USERNAME)}, PASSWORD={bool(SMTP_PASSWORD)}")
        result = {"status": "dry_run", "to": to, "subject": subject}
        logger.info(f"📤 Dry run result: {result}")
        print(f"[DEBUG EMAILER] Returning dry run result: {result}")
        logger.info(f"📤 (Body not included in result to avoid serialization issues)")
        return result

    try:
        logger.info(f"📡 Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            logger.info("🔐 Starting TLS...")
            server.starttls()
            logger.info(f"🔑 Logging in as {SMTP_USERNAME}...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            logger.info(f"📨 Sending email from {SMTP_FROM} to {to}...")
            server.sendmail(SMTP_FROM, [to], msg.as_string())
        logger.info("✅ Email sent successfully!")
        result = {"status": "sent", "to": to}
        logger.info(f"📤 Success result: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        result = {"status": "error", "error": str(e), "to": to}
        logger.info(f"📤 Error result: {result}")
        return result


EmailTool = FunctionTool(func=send_email)