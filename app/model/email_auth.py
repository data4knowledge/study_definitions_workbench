"""Email-code (magic code) authentication.

Replaces the Auth0 OAuth flow. A short numeric code is emailed to the
user; once verified, the route layer populates ``request.session`` with
the same ``userinfo`` structure Auth0 used, so nothing downstream changes.

Pending codes are held in process memory. This is fine for a single
instance; if the app is ever run with multiple workers/instances a code
generated on one will not verify on another. Move the store to the
database (or Redis) if that becomes the deployment model.
"""

import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from d4k_ms_base.logger import application_logger

from app.configuration.configuration import application_configuration as cfg

# email (lower-cased) -> {"code": str, "expires_at": datetime}
_pending_codes: dict[str, dict] = {}


def generate_code(email: str) -> str:
    """Generate, store and return a login code for the given email.

    In dev mode with a configured ``dev_login_code`` the fixed code is
    used (deterministic logins for Playwright). This path is impossible
    in production because ``email_dev_mode`` is off there.
    """
    if cfg.email_dev_mode and cfg.dev_login_code:
        code = cfg.dev_login_code
    else:
        code = "".join(secrets.choice("0123456789") for _ in range(cfg.code_length))
    _pending_codes[email.lower()] = {
        "code": code,
        "expires_at": datetime.now(timezone.utc)
        + timedelta(minutes=cfg.code_expiry_minutes),
    }
    return code


def verify_code(email: str, submitted_code: str) -> bool:
    """Verify a submitted code (constant-time). Consumes it on success."""
    email = email.lower()
    pending = _pending_codes.get(email)
    if not pending:
        return False
    if datetime.now(timezone.utc) > pending["expires_at"]:
        _pending_codes.pop(email, None)
        return False
    if not secrets.compare_digest(pending["code"], (submitted_code or "").strip()):
        return False
    _pending_codes.pop(email, None)
    return True


def send_code_email(email: str, code: str) -> bool:
    """Email the login code, or log it in dev mode. Returns success."""
    if cfg.email_dev_mode:
        application_logger.info(f"[DEV MODE] Login code for {email}: {code}")
        return True
    try:
        body = (
            f"Your {cfg.app_name} login code is: {code}\n\n"
            f"This code expires in {cfg.code_expiry_minutes} minutes.\n"
            f"If you did not request this, you can safely ignore this email."
        )
        msg = MIMEText(body)
        msg["Subject"] = f"{cfg.app_name} login code"
        msg["From"] = cfg.smtp_from
        msg["To"] = email
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            server.starttls()
            if cfg.smtp_user and cfg.smtp_password:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.sendmail(cfg.smtp_from, [email], msg.as_string())
        application_logger.info(f"Login code emailed to {email}")
        return True
    except Exception as e:
        application_logger.exception(f"Failed to send login code to {email}", e)
        return False


def send_registration_notification(new_email: str, name: str) -> bool:
    """Notify the configured address that someone has self-registered.

    Best-effort: returns True if sent (or logged in dev mode), False on
    error. No-op (returns False) if no notify address is configured.
    """
    notify = cfg.registration_notify_email
    if not notify:
        return False
    if cfg.email_dev_mode:
        application_logger.info(
            f"[DEV MODE] New registration: {name} <{new_email}> "
            f"(would notify {notify})"
        )
        return True
    try:
        body = (
            f"A new user has registered with {cfg.app_name}.\n\n"
            f"Name:  {name}\n"
            f"Email: {new_email}\n"
        )
        msg = MIMEText(body)
        msg["Subject"] = f"{cfg.app_name} — new registration: {new_email}"
        msg["From"] = cfg.smtp_from
        msg["To"] = notify
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            server.starttls()
            if cfg.smtp_user and cfg.smtp_password:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.sendmail(cfg.smtp_from, [notify], msg.as_string())
        application_logger.info(f"Registration notification sent to {notify}")
        return True
    except Exception as e:
        application_logger.exception(
            f"Failed to send registration notification to {notify}", e
        )
        return False
