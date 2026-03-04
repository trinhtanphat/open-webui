"""
Billing email notification utilities.

Sends transactional emails for billing events such as:
- Top-up request submitted
- Top-up approved / rejected
- Invoice issued
- Low credit warning

Requires SMTP configuration via environment variables or admin settings.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration – sourced from env.py / config.py via app.state.config
# ---------------------------------------------------------------------------

CURRENCY_SYMBOLS = {
    "USD": "$", "VND": "₫", "EUR": "€", "GBP": "£", "JPY": "¥",
    "CNY": "¥", "KRW": "₩", "SGD": "S$", "THB": "฿", "AUD": "A$",
    "CAD": "C$", "INR": "₹", "MYR": "RM", "PHP": "₱", "IDR": "Rp",
    "TWD": "NT$", "HKD": "HK$", "CHF": "Fr", "BRL": "R$",
}


def _fmt_amount(amount: float, currency: str = "USD") -> str:
    sym = CURRENCY_SYMBOLS.get(currency, currency)
    return f"{sym}{amount:,.2f} {currency}"


def _base_html(title: str, body: str, footer: str = "") -> str:
    """Wraps body content in a clean transactional email HTML template."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body {{ margin:0; padding:0; background:#f4f4f7; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; }}
.container {{ max-width:560px; margin:40px auto; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
.header {{ background:linear-gradient(135deg,#3b82f6,#8b5cf6); padding:28px 32px; color:#fff; }}
.header h1 {{ margin:0; font-size:20px; font-weight:600; }}
.body {{ padding:28px 32px; color:#374151; line-height:1.6; font-size:14px; }}
.body h2 {{ font-size:16px; margin:0 0 16px; color:#111827; }}
.info-table {{ width:100%; border-collapse:collapse; margin:16px 0; }}
.info-table td {{ padding:8px 0; vertical-align:top; }}
.info-table .label {{ color:#6b7280; font-size:13px; width:130px; }}
.info-table .value {{ font-weight:500; font-size:14px; }}
.badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; }}
.badge-success {{ background:#d1fae5; color:#065f46; }}
.badge-warning {{ background:#fef3c7; color:#92400e; }}
.badge-danger {{ background:#fee2e2; color:#991b1b; }}
.badge-info {{ background:#dbeafe; color:#1e40af; }}
.footer {{ padding:20px 32px; background:#f9fafb; color:#9ca3af; font-size:12px; text-align:center; border-top:1px solid #f3f4f6; }}
.footer a {{ color:#6b7280; text-decoration:none; }}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>{title}</h1></div>
<div class="body">{body}</div>
<div class="footer">{footer or 'This is an automated notification from your Open WebUI billing system.'}</div>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_billing_email(
    *,
    to_email: str,
    subject: str,
    html_body: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    smtp_tls: bool = True,
) -> bool:
    """Send a transactional email via SMTP. Returns True on success."""
    if not smtp_host or not to_email:
        log.warning("Email not sent: SMTP host or recipient missing")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from or smtp_user
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if smtp_tls and smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            if smtp_tls:
                server.starttls()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        log.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {e}")
        return False


def _get_smtp_config(app_config) -> dict:
    """Extract SMTP settings from app.state.config."""
    return {
        "smtp_host": getattr(app_config, "SMTP_HOST", "") or "",
        "smtp_port": int(getattr(app_config, "SMTP_PORT", 587) or 587),
        "smtp_user": getattr(app_config, "SMTP_USER", "") or "",
        "smtp_password": getattr(app_config, "SMTP_PASSWORD", "") or "",
        "smtp_from": getattr(app_config, "SMTP_FROM", "") or "",
        "smtp_tls": bool(getattr(app_config, "SMTP_TLS", True)),
    }


def _is_smtp_configured(app_config) -> bool:
    """Check if SMTP is properly configured."""
    cfg = _get_smtp_config(app_config)
    return bool(cfg["smtp_host"])


# ---------------------------------------------------------------------------
# Event-specific email builders
# ---------------------------------------------------------------------------

def notify_topup_submitted(
    *,
    app_config,
    user_email: str,
    user_name: str,
    amount: float,
    currency: str,
    tx_ref: str = "",
    topup_id: str = "",
):
    """Notify user that their top-up request has been submitted."""
    if not _is_smtp_configured(app_config):
        return

    body = f"""\
<h2>Top-up Request Received</h2>
<p>Hi {user_name},</p>
<p>We've received your top-up request and it's being processed.</p>
<table class="info-table">
<tr><td class="label">Amount</td><td class="value">{_fmt_amount(amount, currency)}</td></tr>
<tr><td class="label">Reference</td><td class="value">{tx_ref or '—'}</td></tr>
<tr><td class="label">Request ID</td><td class="value" style="font-family:monospace;font-size:12px">{topup_id}</td></tr>
<tr><td class="label">Status</td><td class="value"><span class="badge badge-warning">Pending</span></td></tr>
</table>
<p>You'll receive another email once your request has been reviewed.</p>"""

    send_billing_email(
        to_email=user_email,
        subject=f"Top-up Request Received – {_fmt_amount(amount, currency)}",
        html_body=_base_html("Top-up Request Received", body),
        **_get_smtp_config(app_config),
    )


def notify_topup_approved(
    *,
    app_config,
    user_email: str,
    user_name: str,
    amount: float,
    currency: str,
    credits: int,
    topup_id: str = "",
    note: str = "",
):
    """Notify user that their top-up has been approved and credits added."""
    if not _is_smtp_configured(app_config):
        return

    body = f"""\
<h2>Top-up Approved ✓</h2>
<p>Hi {user_name},</p>
<p>Great news! Your top-up request has been approved and credits have been added to your account.</p>
<table class="info-table">
<tr><td class="label">Amount</td><td class="value">{_fmt_amount(amount, currency)}</td></tr>
<tr><td class="label">Credits Added</td><td class="value" style="color:#059669;font-weight:700">+{credits:,}</td></tr>
<tr><td class="label">Request ID</td><td class="value" style="font-family:monospace;font-size:12px">{topup_id}</td></tr>
<tr><td class="label">Status</td><td class="value"><span class="badge badge-success">Approved</span></td></tr>
{f'<tr><td class="label">Note</td><td class="value">{note}</td></tr>' if note else ''}
</table>
<p>You can start using your credits immediately in the Developer Console.</p>"""

    send_billing_email(
        to_email=user_email,
        subject=f"Top-up Approved – {credits:,} credits added",
        html_body=_base_html("Top-up Approved", body),
        **_get_smtp_config(app_config),
    )


def notify_topup_rejected(
    *,
    app_config,
    user_email: str,
    user_name: str,
    amount: float,
    currency: str,
    topup_id: str = "",
    note: str = "",
):
    """Notify user that their top-up has been rejected."""
    if not _is_smtp_configured(app_config):
        return

    body = f"""\
<h2>Top-up Request Declined</h2>
<p>Hi {user_name},</p>
<p>Unfortunately, your top-up request could not be approved.</p>
<table class="info-table">
<tr><td class="label">Amount</td><td class="value">{_fmt_amount(amount, currency)}</td></tr>
<tr><td class="label">Request ID</td><td class="value" style="font-family:monospace;font-size:12px">{topup_id}</td></tr>
<tr><td class="label">Status</td><td class="value"><span class="badge badge-danger">Rejected</span></td></tr>
{f'<tr><td class="label">Reason</td><td class="value">{note}</td></tr>' if note else ''}
</table>
<p>If you believe this is an error, please contact the administrator.</p>"""

    send_billing_email(
        to_email=user_email,
        subject=f"Top-up Request Declined – {_fmt_amount(amount, currency)}",
        html_body=_base_html("Top-up Request Declined", body),
        **_get_smtp_config(app_config),
    )


def notify_invoice_issued(
    *,
    app_config,
    user_email: str,
    user_name: str,
    invoice_id: str,
    amount: float,
    currency: str,
    credits: int,
):
    """Notify user that an invoice has been issued."""
    if not _is_smtp_configured(app_config):
        return

    body = f"""\
<h2>Invoice Issued</h2>
<p>Hi {user_name},</p>
<p>A new invoice has been generated for your account.</p>
<table class="info-table">
<tr><td class="label">Invoice ID</td><td class="value" style="font-family:monospace;font-size:12px">{invoice_id}</td></tr>
<tr><td class="label">Amount</td><td class="value">{_fmt_amount(amount, currency)}</td></tr>
<tr><td class="label">Credits</td><td class="value">{credits:,}</td></tr>
<tr><td class="label">Status</td><td class="value"><span class="badge badge-info">Issued</span></td></tr>
</table>
<p>You can view your invoices in the Developer Console.</p>"""

    send_billing_email(
        to_email=user_email,
        subject=f"Invoice #{invoice_id[:8]} – {_fmt_amount(amount, currency)}",
        html_body=_base_html("Invoice Issued", body),
        **_get_smtp_config(app_config),
    )


def notify_low_credits(
    *,
    app_config,
    user_email: str,
    user_name: str,
    credits_remaining: int,
    threshold: int = 100,
):
    """Warn user when their credits are running low."""
    if not _is_smtp_configured(app_config):
        return

    body = f"""\
<h2>Low Credit Warning ⚠</h2>
<p>Hi {user_name},</p>
<p>Your API credit balance is running low.</p>
<table class="info-table">
<tr><td class="label">Credits Remaining</td><td class="value" style="color:#dc2626;font-weight:700">{credits_remaining:,}</td></tr>
<tr><td class="label">Threshold</td><td class="value">{threshold:,}</td></tr>
</table>
<p>Top up your account in the Developer Console to avoid service interruption.</p>"""

    send_billing_email(
        to_email=user_email,
        subject=f"Low Credit Warning – {credits_remaining:,} credits remaining",
        html_body=_base_html("Low Credit Warning", body),
        **_get_smtp_config(app_config),
    )


def notify_admin_new_topup(
    *,
    app_config,
    admin_email: str,
    user_name: str,
    user_email: str,
    amount: float,
    currency: str,
    topup_id: str = "",
):
    """Notify admin about a new pending top-up request."""
    if not _is_smtp_configured(app_config):
        return

    body = f"""\
<h2>New Top-up Request</h2>
<p>A user has submitted a new top-up request that requires your attention.</p>
<table class="info-table">
<tr><td class="label">User</td><td class="value">{user_name} ({user_email})</td></tr>
<tr><td class="label">Amount</td><td class="value">{_fmt_amount(amount, currency)}</td></tr>
<tr><td class="label">Request ID</td><td class="value" style="font-family:monospace;font-size:12px">{topup_id}</td></tr>
<tr><td class="label">Status</td><td class="value"><span class="badge badge-warning">Pending Review</span></td></tr>
</table>
<p>Please review this request in the Admin → API Keys → Top-ups tab.</p>"""

    send_billing_email(
        to_email=admin_email,
        subject=f"New Top-up Request from {user_name} – {_fmt_amount(amount, currency)}",
        html_body=_base_html("New Top-up Request", body),
        **_get_smtp_config(app_config),
    )
