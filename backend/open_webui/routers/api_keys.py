import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from open_webui.internal.db import get_session
from open_webui.models.billing import Billing
from open_webui.models.users import Users
from open_webui.utils.auth import create_api_key, get_admin_user, get_verified_user
from open_webui.utils.email import (
    notify_topup_submitted,
    notify_topup_approved,
    notify_topup_rejected,
    notify_invoice_issued,
    notify_admin_new_topup,
)

log = logging.getLogger(__name__)

router = APIRouter()


class ApiKeyConsoleResponse(BaseModel):
    id: str
    user_id: str
    key: str
    key_masked: str
    status: str
    plan_name: Optional[str] = None
    monthly_price_usd: Optional[float] = None
    credits_remaining: int = 0
    total_requests: int = 0
    monthly_requests: int = 0
    usage_month: Optional[str] = None
    last_used_at: Optional[int] = None
    expires_at: Optional[int] = None
    created_at: int
    updated_at: int


class AdminCreateApiKeyForm(BaseModel):
    user_id: str
    plan_name: Optional[str] = "starter"
    monthly_price_usd: Optional[float] = 0
    credits: int = 1000
    expires_at: Optional[int] = None


class ApiKeyCreditsUpdateForm(BaseModel):
    delta: int
    note: Optional[str] = None


class ApiKeyStatusUpdateForm(BaseModel):
    status: str


class ApiKeyPlanUpdateForm(BaseModel):
    plan_name: Optional[str] = None
    monthly_price_usd: Optional[float] = None
    credits_reset_to: Optional[int] = None


class PaymentAccountForm(BaseModel):
    provider: str
    account_name: str
    account_number: str
    qr_code_url: Optional[str] = None
    instructions: Optional[str] = None
    metadata: Optional[dict] = None


class PaymentAccountUpdateForm(BaseModel):
    provider: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    qr_code_url: Optional[str] = None
    instructions: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None


class TopupRequestForm(BaseModel):
    api_key_id: str
    payment_account_id: str
    amount: float
    currency: str = "USD"
    tx_ref: Optional[str] = None
    note: Optional[str] = None


class TopupReviewForm(BaseModel):
    credits: int
    note: Optional[str] = None


class TopupRejectForm(BaseModel):
    note: Optional[str] = None


class BillingSettingsResponse(BaseModel):
    auto_approve_topups: bool
    default_currency: str
    enable_billing_emails: bool = True


class BillingSettingsUpdateForm(BaseModel):
    auto_approve_topups: bool
    default_currency: Optional[str] = None
    enable_billing_emails: Optional[bool] = None


class SmtpSettingsResponse(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True
    enable_billing_emails: bool = True


class SmtpSettingsUpdateForm(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: Optional[str] = None
    smtp_from: str = ""
    smtp_tls: bool = True
    enable_billing_emails: bool = True


class BillingSummaryResponse(BaseModel):
    total_keys: int
    active_keys: int
    total_credits_remaining: int
    pending_topups: int
    paid_invoices: int
    total_revenue: float


class RevenueDailyEntry(BaseModel):
    date: str
    revenue: float
    credits: int
    invoices: int


class ApiKeyPlan(BaseModel):
    id: str
    name: str
    monthly_price_usd: float
    included_credits: int
    rpm_limit: int
    overage_usd_per_1k_requests: float
    support_tier: str
    recommended_for: str


class UserUsageSummary(BaseModel):
    plan_name: Optional[str] = None
    monthly_price_usd: Optional[float] = None
    credits_remaining: int = 0
    total_requests: int = 0
    monthly_requests: int = 0
    usage_month: Optional[str] = None
    last_used_at: Optional[int] = None
    pending_topups: int = 0
    approved_topups: int = 0
    rejected_topups: int = 0
    paid_invoices: int = 0
    total_spend_usd: float = 0
    avg_spend_per_1k_requests_usd: float = 0


class PaymentWebhookForm(BaseModel):
    topup_request_id: str
    status: str
    payment_account_id: Optional[str] = None
    tx_ref: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    credits: Optional[int] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Model Pricing forms
# ---------------------------------------------------------------------------
class ModelPricingForm(BaseModel):
    model_id: str
    display_name: Optional[str] = None
    input_cost_per_1k_tokens: float = 0.0
    output_cost_per_1k_tokens: float = 0.0
    per_request_cost: float = 0.0
    currency: str = "USD"


class ModelPricingUpdateForm(BaseModel):
    model_id: Optional[str] = None
    display_name: Optional[str] = None
    input_cost_per_1k_tokens: Optional[float] = None
    output_cost_per_1k_tokens: Optional[float] = None
    per_request_cost: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class UsageDailySummaryEntry(BaseModel):
    date: str
    requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float


class UsageByModelEntry(BaseModel):
    model: str
    requests: int
    total_tokens: int
    total_cost: float


API_KEY_PLANS: list[ApiKeyPlan] = [
    ApiKeyPlan(
        id="starter",
        name="Starter",
        monthly_price_usd=19,
        included_credits=5000,
        rpm_limit=30,
        overage_usd_per_1k_requests=0.3,
        support_tier="Community",
        recommended_for="MVP and personal projects",
    ),
    ApiKeyPlan(
        id="pro",
        name="Pro",
        monthly_price_usd=79,
        included_credits=30000,
        rpm_limit=120,
        overage_usd_per_1k_requests=0.25,
        support_tier="Priority",
        recommended_for="Growing products and small teams",
    ),
    ApiKeyPlan(
        id="business",
        name="Business",
        monthly_price_usd=249,
        included_credits=120000,
        rpm_limit=300,
        overage_usd_per_1k_requests=0.2,
        support_tier="Dedicated",
        recommended_for="Production workloads and enterprise integrations",
    ),
]


def _mask_key(key: str, is_full: bool = True) -> str:
    """Mask an API key for display.
    
    When is_full=True  (full key available): sk-abc123...wxyz  (show first 7 + last 4)
    When is_full=False (only prefix stored):  sk-abc1***...    (show prefix + stars)
    """
    if is_full and len(key) > 12:
        return f"{key[:7]}{'*' * 32}...{key[-4:]}"
    # prefix-only: show what we have + stars
    return f"{key}{'*' * 40}..."


def _build_console_payload(record, full_key: str = None) -> ApiKeyConsoleResponse:
    metadata = record.data if isinstance(record.data, dict) else {}
    has_full = full_key is not None
    display_key = full_key if full_key else record.key
    return ApiKeyConsoleResponse(
        id=record.id,
        user_id=record.user_id,
        key=display_key if has_full else "",
        key_masked=_mask_key(display_key, is_full=has_full),
        status=metadata.get("status", "active"),
        plan_name=metadata.get("plan_name"),
        monthly_price_usd=metadata.get("monthly_price_usd"),
        credits_remaining=int(metadata.get("credits_remaining", 0)),
        total_requests=int(metadata.get("total_requests", 0)),
        monthly_requests=int(metadata.get("monthly_requests", 0)),
        usage_month=metadata.get("usage_month"),
        last_used_at=record.last_used_at,
        expires_at=record.expires_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _build_usage_summary(user_id: str, record, db: Session) -> UserUsageSummary:
    metadata = record.data if record and isinstance(record.data, dict) else {}

    topups = Billing.get_topup_requests(user_id=user_id, db=db)
    pending_topups = len([item for item in topups if item.status == "pending"])
    approved_topups = len([item for item in topups if item.status == "approved"])
    rejected_topups = len([item for item in topups if item.status == "rejected"])

    invoices = Billing.get_invoices(user_id=user_id, db=db)
    paid = [item for item in invoices if item.status == "paid"]
    total_spend = float(sum(item.amount for item in paid))

    total_requests = int(metadata.get("total_requests", 0))
    avg_spend_per_1k_requests = 0.0
    if total_requests > 0:
        avg_spend_per_1k_requests = round((total_spend / total_requests) * 1000, 4)

    return UserUsageSummary(
        plan_name=metadata.get("plan_name"),
        monthly_price_usd=metadata.get("monthly_price_usd"),
        credits_remaining=int(metadata.get("credits_remaining", 0)),
        total_requests=total_requests,
        monthly_requests=int(metadata.get("monthly_requests", 0)),
        usage_month=metadata.get("usage_month"),
        last_used_at=record.last_used_at if record else None,
        pending_topups=pending_topups,
        approved_topups=approved_topups,
        rejected_topups=rejected_topups,
        paid_invoices=len(paid),
        total_spend_usd=round(total_spend, 4),
        avg_spend_per_1k_requests_usd=avg_spend_per_1k_requests,
    )


@router.get("/plans", response_model=list[ApiKeyPlan])
async def get_api_key_plans(user=Depends(get_verified_user)):
    return API_KEY_PLANS


class SelfActivateForm(BaseModel):
    plan_id: Optional[str] = "starter"


@router.post("/me/activate", response_model=ApiKeyConsoleResponse)
async def self_activate_api_key(
    form_data: SelfActivateForm = SelfActivateForm(),
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    """Self-service API key activation.
    
    Users can activate their own API key without admin approval.
    They get the default (starter) plan with included credits.
    No admin gate — any verified user can activate.
    """
    existing = Users.get_user_api_key_record_by_id(user.id, db=db)
    if existing:
        raise HTTPException(status_code=400, detail="API key already exists. Use regenerate instead.")

    plan = next((p for p in API_KEY_PLANS if p.id == form_data.plan_id), API_KEY_PLANS[0])

    key = create_api_key()
    success = Users.update_user_api_key_by_id(user.id, key, db=db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create API key")

    record = Users.get_user_api_key_record_by_id(user.id, db=db)
    if not record:
        raise HTTPException(status_code=500, detail="Failed to load API key")

    metadata = {
        "status": "active",
        "plan_name": plan.id,
        "monthly_price_usd": plan.monthly_price_usd,
        "credits_remaining": max(0, plan.included_credits),
        "rpm_limit": plan.rpm_limit,
        "total_requests": 0,
        "monthly_requests": 0,
        "usage_month": time.strftime("%Y-%m", time.gmtime()),
        "activated_by": "self",
    }

    updated = Users.update_api_key_by_id(
        record.id,
        {
            "data": metadata,
        },
        db=db,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to initialize API key")

    return _build_console_payload(updated, full_key=key)


@router.get("/me", response_model=ApiKeyConsoleResponse)
async def get_my_api_key_console(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    record = Users.get_user_api_key_record_by_id(user.id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")

    return _build_console_payload(record)


@router.get("/me/usage", response_model=UserUsageSummary)
async def get_my_usage_summary(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    record = Users.get_user_api_key_record_by_id(user.id, db=db)
    return _build_usage_summary(user.id, record, db)


@router.post("/me/regenerate", response_model=ApiKeyConsoleResponse)
async def regenerate_my_api_key(
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    old_record = Users.get_user_api_key_record_by_id(user.id, db=db)
    metadata = old_record.data if old_record and isinstance(old_record.data, dict) else {}

    new_key = create_api_key()
    success = Users.update_user_api_key_by_id(user.id, new_key, db=db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to regenerate API key")

    new_record = Users.get_user_api_key_record_by_id(user.id, db=db)
    if not new_record:
        raise HTTPException(status_code=500, detail="Failed to load regenerated API key")

    if metadata:
        Users.update_api_key_by_id(
            new_record.id,
            {
                "data": metadata,
                "expires_at": metadata.get("expires_at") or new_record.expires_at,
            },
            db=db,
        )
        new_record = Users.get_user_api_key_record_by_id(user.id, db=db)

    return _build_console_payload(new_record, full_key=new_key)


@router.get("/admin/keys", response_model=list[ApiKeyConsoleResponse])
async def get_admin_api_keys(user=Depends(get_admin_user), db: Session = Depends(get_session)):
    records = Users.get_api_keys(db=db)
    return [_build_console_payload(record) for record in records]


@router.get("/admin/summary", response_model=BillingSummaryResponse)
async def get_admin_billing_summary(
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    key_rows = Users.get_api_keys(db=db)
    topups = Billing.get_topup_requests(status="pending", db=db)
    invoices = Billing.get_invoices(db=db)

    active_keys = 0
    total_credits_remaining = 0
    for key in key_rows:
        metadata = key.data if isinstance(key.data, dict) else {}
        if metadata.get("status", "active") == "active":
            active_keys += 1
        total_credits_remaining += int(metadata.get("credits_remaining", 0))

    paid_invoices = [invoice for invoice in invoices if invoice.status == "paid"]
    total_revenue = sum(invoice.amount for invoice in paid_invoices)

    return BillingSummaryResponse(
        total_keys=len(key_rows),
        active_keys=active_keys,
        total_credits_remaining=total_credits_remaining,
        pending_topups=len(topups),
        paid_invoices=len(paid_invoices),
        total_revenue=total_revenue,
    )


@router.post("/admin/keys", response_model=ApiKeyConsoleResponse)
async def admin_create_api_key(
    form_data: AdminCreateApiKeyForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    target_user = Users.get_user_by_id(form_data.user_id, db=db)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    key = create_api_key()
    success = Users.update_user_api_key_by_id(form_data.user_id, key, db=db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create API key")

    record = Users.get_user_api_key_record_by_id(form_data.user_id, db=db)
    if not record:
        raise HTTPException(status_code=500, detail="Failed to load API key")

    metadata = {
        "status": "active",
        "plan_name": form_data.plan_name,
        "monthly_price_usd": form_data.monthly_price_usd,
        "credits_remaining": max(0, int(form_data.credits)),
        "total_requests": 0,
        "monthly_requests": 0,
        "usage_month": time.strftime("%Y-%m", time.gmtime()),
        "updated_by_admin": user.id,
    }

    updated = Users.update_api_key_by_id(
        record.id,
        {
            "data": metadata,
            "expires_at": form_data.expires_at,
        },
        db=db,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to initialize API key metadata")

    return _build_console_payload(updated, full_key=key)


@router.post("/admin/keys/{key_id}/credits", response_model=ApiKeyConsoleResponse)
async def admin_update_credits(
    key_id: str,
    form_data: ApiKeyCreditsUpdateForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    record = Users.get_api_key_record_by_id(key_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")

    metadata = record.data if isinstance(record.data, dict) else {}
    current = int(metadata.get("credits_remaining", 0))
    metadata["credits_remaining"] = max(0, current + int(form_data.delta))
    metadata["last_credit_note"] = form_data.note
    metadata["updated_by_admin"] = user.id

    updated = Users.update_api_key_by_id(key_id, {"data": metadata}, db=db)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update credits")

    return _build_console_payload(updated)


@router.post("/admin/keys/{key_id}/status", response_model=ApiKeyConsoleResponse)
async def admin_update_status(
    key_id: str,
    form_data: ApiKeyStatusUpdateForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    if form_data.status not in {"active", "suspended"}:
        raise HTTPException(status_code=400, detail="Status must be active or suspended")

    record = Users.get_api_key_record_by_id(key_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")

    metadata = record.data if isinstance(record.data, dict) else {}
    metadata["status"] = form_data.status
    metadata["updated_by_admin"] = user.id

    updated = Users.update_api_key_by_id(key_id, {"data": metadata}, db=db)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update status")

    return _build_console_payload(updated)


@router.post("/admin/keys/{key_id}/plan", response_model=ApiKeyConsoleResponse)
async def admin_update_plan(
    key_id: str,
    form_data: ApiKeyPlanUpdateForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    record = Users.get_api_key_record_by_id(key_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")

    metadata = record.data if isinstance(record.data, dict) else {}

    if form_data.plan_name is not None:
        metadata["plan_name"] = form_data.plan_name
    if form_data.monthly_price_usd is not None:
        metadata["monthly_price_usd"] = form_data.monthly_price_usd
    if form_data.credits_reset_to is not None:
        metadata["credits_remaining"] = max(0, int(form_data.credits_reset_to))

    metadata["updated_by_admin"] = user.id

    updated = Users.update_api_key_by_id(key_id, {"data": metadata}, db=db)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update plan")

    return _build_console_payload(updated)


@router.get("/admin/payment-accounts")
async def get_admin_payment_accounts(user=Depends(get_admin_user), db: Session = Depends(get_session)):
    return Billing.get_payment_accounts(include_inactive=True, db=db)


@router.get("/settings", response_model=BillingSettingsResponse)
async def get_billing_settings(user=Depends(get_verified_user), request: Request = None):
    return BillingSettingsResponse(
        auto_approve_topups=bool(request.app.state.config.BILLING_AUTO_APPROVE_TOPUPS),
        default_currency=str(request.app.state.config.BILLING_DEFAULT_CURRENCY),
        enable_billing_emails=bool(getattr(request.app.state.config, "ENABLE_BILLING_EMAILS", True)),
    )


@router.get("/admin/settings", response_model=BillingSettingsResponse)
async def get_admin_billing_settings(user=Depends(get_admin_user), request: Request = None):
    return BillingSettingsResponse(
        auto_approve_topups=bool(request.app.state.config.BILLING_AUTO_APPROVE_TOPUPS),
        default_currency=str(request.app.state.config.BILLING_DEFAULT_CURRENCY),
        enable_billing_emails=bool(getattr(request.app.state.config, "ENABLE_BILLING_EMAILS", True)),
    )


@router.post("/admin/settings", response_model=BillingSettingsResponse)
async def update_admin_billing_settings(
    form_data: BillingSettingsUpdateForm,
    user=Depends(get_admin_user),
    request: Request = None,
):
    request.app.state.config.BILLING_AUTO_APPROVE_TOPUPS = bool(form_data.auto_approve_topups)
    if form_data.default_currency is not None:
        request.app.state.config.BILLING_DEFAULT_CURRENCY = form_data.default_currency
    if form_data.enable_billing_emails is not None:
        request.app.state.config.ENABLE_BILLING_EMAILS = bool(form_data.enable_billing_emails)
    return BillingSettingsResponse(
        auto_approve_topups=bool(request.app.state.config.BILLING_AUTO_APPROVE_TOPUPS),
        default_currency=str(request.app.state.config.BILLING_DEFAULT_CURRENCY),
        enable_billing_emails=bool(getattr(request.app.state.config, "ENABLE_BILLING_EMAILS", True)),
    )


# --- SMTP Settings (admin only) ---

@router.get("/admin/smtp", response_model=SmtpSettingsResponse)
async def get_admin_smtp_settings(user=Depends(get_admin_user), request: Request = None):
    cfg = request.app.state.config
    return SmtpSettingsResponse(
        smtp_host=str(getattr(cfg, "SMTP_HOST", "") or ""),
        smtp_port=int(getattr(cfg, "SMTP_PORT", 587) or 587),
        smtp_user=str(getattr(cfg, "SMTP_USER", "") or ""),
        smtp_from=str(getattr(cfg, "SMTP_FROM", "") or ""),
        smtp_tls=bool(getattr(cfg, "SMTP_TLS", True)),
        enable_billing_emails=bool(getattr(cfg, "ENABLE_BILLING_EMAILS", True)),
    )


@router.post("/admin/smtp", response_model=SmtpSettingsResponse)
async def update_admin_smtp_settings(
    form_data: SmtpSettingsUpdateForm,
    user=Depends(get_admin_user),
    request: Request = None,
):
    cfg = request.app.state.config
    cfg.SMTP_HOST = form_data.smtp_host
    cfg.SMTP_PORT = form_data.smtp_port
    cfg.SMTP_USER = form_data.smtp_user
    if form_data.smtp_password is not None:
        cfg.SMTP_PASSWORD = form_data.smtp_password
    cfg.SMTP_FROM = form_data.smtp_from
    cfg.SMTP_TLS = form_data.smtp_tls
    cfg.ENABLE_BILLING_EMAILS = form_data.enable_billing_emails
    return SmtpSettingsResponse(
        smtp_host=str(cfg.SMTP_HOST or ""),
        smtp_port=int(cfg.SMTP_PORT or 587),
        smtp_user=str(cfg.SMTP_USER or ""),
        smtp_from=str(cfg.SMTP_FROM or ""),
        smtp_tls=bool(cfg.SMTP_TLS),
        enable_billing_emails=bool(cfg.ENABLE_BILLING_EMAILS),
    )


@router.post("/admin/smtp/test")
async def test_smtp_settings(user=Depends(get_admin_user), request: Request = None):
    """Send a test email to verify SMTP configuration."""
    from open_webui.utils.email import send_billing_email, _base_html, _get_smtp_config

    cfg = request.app.state.config
    smtp_cfg = _get_smtp_config(cfg)
    if not smtp_cfg["smtp_host"]:
        raise HTTPException(status_code=400, detail="SMTP not configured")

    target_email = user.email
    if not target_email:
        raise HTTPException(status_code=400, detail="Admin user has no email address")

    body = "<h2>SMTP Test Successful</h2><p>If you're reading this, your email configuration is working correctly.</p>"
    ok = send_billing_email(
        to_email=target_email,
        subject="Open WebUI – SMTP Test",
        html_body=_base_html("SMTP Test", body),
        **smtp_cfg,
    )
    if ok:
        return {"status": "ok", "message": f"Test email sent to {target_email}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check SMTP configuration and logs.")


@router.post("/admin/payment-accounts")
async def create_admin_payment_account(
    form_data: PaymentAccountForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    row = Billing.create_payment_account(
        provider=form_data.provider,
        account_name=form_data.account_name,
        account_number=form_data.account_number,
        qr_code_url=form_data.qr_code_url,
        instructions=form_data.instructions,
        metadata=form_data.metadata,
        actor_id=user.id,
        db=db,
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create payment account")

    Billing.log_audit(
        actor_id=user.id,
        action="payment_account.create",
        target_type="payment_account",
        target_id=row.id,
        details={"provider": row.provider, "account_name": row.account_name},
        db=db,
    )

    return row


@router.post("/admin/payment-accounts/{account_id}")
async def update_admin_payment_account(
    account_id: str,
    form_data: PaymentAccountUpdateForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    updated_data = form_data.model_dump(exclude_none=True)
    if "is_active" in updated_data:
        updated_data["is_active"] = "true" if updated_data["is_active"] else "false"

    row = Billing.update_payment_account(account_id, updated_data, actor_id=user.id, db=db)
    if not row:
        raise HTTPException(status_code=404, detail="Payment account not found")

    Billing.log_audit(
        actor_id=user.id,
        action="payment_account.update",
        target_type="payment_account",
        target_id=row.id,
        details={"updated": updated_data},
        db=db,
    )

    return row


@router.get("/admin/topups")
async def get_admin_topups(
    status: Optional[str] = None,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    rows = Billing.get_topup_requests(status=status, db=db)
    # Enrich with user names
    user_ids = list({r.user_id for r in rows})
    user_map: dict[str, str] = {}
    for uid in user_ids:
        u = Users.get_user_by_id(uid)
        if u:
            user_map[uid] = u.name or u.email or uid[:8]
    result = []
    for r in rows:
        d = r.model_dump()
        d["user_name"] = user_map.get(r.user_id, r.user_id[:8])
        result.append(d)
    return result


@router.post("/admin/topups/{request_id}/approve")
async def approve_topup_request(
    request_id: str,
    request: Request,
    form_data: TopupReviewForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    return _finalize_topup_approval(
        request_id=request_id,
        credits=max(0, int(form_data.credits)),
        reviewed_by=user.id,
        reviewed_note=form_data.note,
        actor_id=user.id,
        actor_action="topup.approve",
        actor_details={"credits": form_data.credits},
        db=db,
        app_config=request.app.state.config,
    )


def _finalize_topup_approval(
    request_id: str,
    credits: int,
    reviewed_by: str,
    reviewed_note: Optional[str],
    actor_id: str,
    actor_action: str,
    actor_details: Optional[dict],
    db: Session,
    app_config=None,
):
    request_row = Billing.get_topup_request_by_id(request_id, db=db)
    if not request_row:
        raise HTTPException(status_code=404, detail="Top-up request not found")

    if request_row.status != "pending":
        raise HTTPException(status_code=400, detail="Top-up request is not pending")

    key_row = Users.get_api_key_record_by_id(request_row.api_key_id, db=db)
    if not key_row:
        raise HTTPException(status_code=404, detail="API key not found")

    metadata = key_row.data if isinstance(key_row.data, dict) else {}
    metadata["credits_remaining"] = int(metadata.get("credits_remaining", 0)) + max(0, int(credits))
    metadata["updated_by_admin"] = reviewed_by

    updated_key = Users.update_api_key_by_id(key_row.id, {"data": metadata}, db=db)
    if not updated_key:
        raise HTTPException(status_code=500, detail="Failed to add credits")

    reviewed = Billing.update_topup_request_status(
        request_id,
        status="approved",
        reviewed_by=reviewed_by,
        reviewed_note=reviewed_note,
        db=db,
    )

    invoice = Billing.create_invoice(
        user_id=request_row.user_id,
        api_key_id=request_row.api_key_id,
        topup_request_id=request_row.id,
        amount=request_row.amount,
        currency=request_row.currency,
        credits=max(0, int(credits)),
        data={"approved_by": reviewed_by, "note": reviewed_note},
        db=db,
    )

    Billing.log_audit(
        actor_id=actor_id,
        action=actor_action,
        target_type="topup_request",
        target_id=request_id,
        details={
            **(actor_details or {}),
            "credits": credits,
            "invoice_id": invoice.id if invoice else None,
        },
        db=db,
    )

    # --- Email notifications ---
    if app_config and getattr(app_config, "ENABLE_BILLING_EMAILS", False):
        try:
            target_user = Users.get_user_by_id(request_row.user_id)
            if target_user and target_user.email:
                notify_topup_approved(
                    app_config=app_config,
                    user_email=target_user.email,
                    user_name=target_user.name or target_user.email,
                    amount=float(request_row.amount),
                    currency=request_row.currency or "USD",
                    credits=credits,
                    topup_id=request_row.id,
                    note=reviewed_note or "",
                )
                if invoice:
                    notify_invoice_issued(
                        app_config=app_config,
                        user_email=target_user.email,
                        user_name=target_user.name or target_user.email,
                        invoice_id=invoice.id,
                        amount=float(request_row.amount),
                        currency=request_row.currency or "USD",
                        credits=credits,
                    )
        except Exception as e:
            log.warning(f"Failed to send topup approval email: {e}")

    return {
        "topup": reviewed,
        "api_key": _build_console_payload(updated_key),
        "invoice": invoice,
    }


@router.post("/admin/topups/{request_id}/reject")
async def reject_topup_request(
    request_id: str,
    request: Request,
    form_data: TopupRejectForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    request_row = Billing.get_topup_request_by_id(request_id, db=db)
    if not request_row:
        raise HTTPException(status_code=404, detail="Top-up request not found")

    if request_row.status != "pending":
        raise HTTPException(status_code=400, detail="Top-up request is not pending")

    reviewed = Billing.update_topup_request_status(
        request_id,
        status="rejected",
        reviewed_by=user.id,
        reviewed_note=form_data.note,
        db=db,
    )

    Billing.log_audit(
        actor_id=user.id,
        action="topup.reject",
        target_type="topup_request",
        target_id=request_id,
        details={"note": form_data.note},
        db=db,
    )

    # --- Email notification ---
    if getattr(request.app.state.config, "ENABLE_BILLING_EMAILS", False):
        try:
            target_user = Users.get_user_by_id(request_row.user_id)
            if target_user and target_user.email:
                notify_topup_rejected(
                    app_config=request.app.state.config,
                    user_email=target_user.email,
                    user_name=target_user.name or target_user.email,
                    amount=float(request_row.amount),
                    currency=request_row.currency or "USD",
                    topup_id=request_row.id,
                    note=form_data.note or "",
                )
        except Exception as e:
            log.warning(f"Failed to send topup rejection email: {e}")

    return reviewed


@router.get("/admin/invoices")
async def get_admin_invoices(user=Depends(get_admin_user), db: Session = Depends(get_session)):
    rows = Billing.get_invoices(db=db)
    # Enrich with user names
    user_ids = list({r.user_id for r in rows})
    user_map: dict[str, str] = {}
    for uid in user_ids:
        u = Users.get_user_by_id(uid)
        if u:
            user_map[uid] = u.name or u.email or uid[:8]
    result = []
    for r in rows:
        d = r.model_dump()
        d["user_name"] = user_map.get(r.user_id, r.user_id[:8])
        result.append(d)
    return result


@router.get("/admin/invoices/{invoice_id}")
async def get_admin_invoice_detail(
    invoice_id: str,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    invoice = Billing.get_invoice_by_id(invoice_id, db=db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/admin/analytics/revenue-daily", response_model=list[RevenueDailyEntry])
async def get_admin_revenue_daily(
    days: int = 30,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    return Billing.get_daily_revenue(days=days, db=db)


@router.get("/admin/audit-logs")
async def get_admin_audit_logs(
    limit: int = 100,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    rows = Billing.get_audit_logs(limit=limit, db=db)
    # Enrich with actor names
    actor_ids = list({r.actor_id for r in rows})
    user_map: dict[str, str] = {}
    for uid in actor_ids:
        u = Users.get_user_by_id(uid)
        if u:
            user_map[uid] = u.name or u.email or uid[:8]
    result = []
    for r in rows:
        d = r.model_dump()
        d["actor_name"] = user_map.get(r.actor_id, r.actor_id[:8])
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Admin – Model Pricing CRUD
# ---------------------------------------------------------------------------
@router.get("/admin/model-pricing")
async def get_admin_model_pricings(
    include_inactive: bool = False,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    return Billing.get_model_pricings(include_inactive=include_inactive, db=db)


@router.post("/admin/model-pricing")
async def create_admin_model_pricing(
    form_data: ModelPricingForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    row = Billing.create_model_pricing(
        model_id=form_data.model_id,
        display_name=form_data.display_name,
        input_cost_per_1k_tokens=form_data.input_cost_per_1k_tokens,
        output_cost_per_1k_tokens=form_data.output_cost_per_1k_tokens,
        per_request_cost=form_data.per_request_cost,
        currency=form_data.currency,
        actor_id=user.id,
        db=db,
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create model pricing (model_id may already exist)")

    Billing.log_audit(
        actor_id=user.id,
        action="model_pricing.create",
        target_type="model_pricing",
        target_id=row.id,
        details={"model_id": row.model_id},
        db=db,
    )
    return row


@router.post("/admin/model-pricing/{pricing_id}")
async def update_admin_model_pricing(
    pricing_id: str,
    form_data: ModelPricingUpdateForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    updated_data = form_data.model_dump(exclude_none=True)
    if "is_active" in updated_data:
        updated_data["is_active"] = "true" if updated_data["is_active"] else "false"

    row = Billing.update_model_pricing(pricing_id, updated_data, actor_id=user.id, db=db)
    if not row:
        raise HTTPException(status_code=404, detail="Model pricing not found")

    Billing.log_audit(
        actor_id=user.id,
        action="model_pricing.update",
        target_type="model_pricing",
        target_id=pricing_id,
        details={"updated": updated_data},
        db=db,
    )
    return row


@router.delete("/admin/model-pricing/{pricing_id}")
async def delete_admin_model_pricing(
    pricing_id: str,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    success = Billing.delete_model_pricing(pricing_id, db=db)
    if not success:
        raise HTTPException(status_code=404, detail="Model pricing not found")

    Billing.log_audit(
        actor_id=user.id,
        action="model_pricing.delete",
        target_type="model_pricing",
        target_id=pricing_id,
        details=None,
        db=db,
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin – Usage Logs
# ---------------------------------------------------------------------------
@router.get("/admin/usage-logs")
async def get_admin_usage_logs(
    user_id: Optional[str] = None,
    model: Optional[str] = None,
    days: int = 30,
    limit: int = 200,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    return Billing.get_usage_logs(
        user_id=user_id, model=model, days=days, limit=limit, db=db
    )


@router.get("/admin/usage-logs/daily", response_model=list[UsageDailySummaryEntry])
async def get_admin_usage_daily_summary(
    user_id: Optional[str] = None,
    days: int = 30,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    return Billing.get_usage_daily_summary(user_id=user_id, days=days, db=db)


@router.get("/admin/usage-logs/by-model", response_model=list[UsageByModelEntry])
async def get_admin_usage_by_model(
    user_id: Optional[str] = None,
    days: int = 30,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
):
    return Billing.get_usage_by_model_summary(user_id=user_id, days=days, db=db)


# ---------------------------------------------------------------------------
# Public – Model Pricing (read-only for users)
# ---------------------------------------------------------------------------
@router.get("/model-pricing")
async def get_public_model_pricing(
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    return Billing.get_model_pricings(include_inactive=False, db=db)


# ---------------------------------------------------------------------------
# User – My Usage Logs
# ---------------------------------------------------------------------------
@router.get("/me/usage-logs")
async def get_my_usage_logs(
    model: Optional[str] = None,
    days: int = 30,
    limit: int = 200,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    return Billing.get_usage_logs(
        user_id=user.id, model=model, days=days, limit=limit, db=db
    )


@router.get("/me/usage-logs/daily", response_model=list[UsageDailySummaryEntry])
async def get_my_usage_daily(
    days: int = 30,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    return Billing.get_usage_daily_summary(user_id=user.id, days=days, db=db)


@router.get("/me/usage-logs/by-model", response_model=list[UsageByModelEntry])
async def get_my_usage_by_model(
    days: int = 30,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    return Billing.get_usage_by_model_summary(user_id=user.id, days=days, db=db)


@router.get("/payment-accounts")
async def get_public_payment_accounts(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    return Billing.get_payment_accounts(include_inactive=False, db=db)


@router.post("/me/topups")
async def create_my_topup_request(
    request: Request,
    form_data: TopupRequestForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    key_row = Users.get_api_key_record_by_id(form_data.api_key_id, db=db)
    if not key_row:
        raise HTTPException(status_code=404, detail="API key not found")
    if key_row.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only create top-ups for your own API key")

    account = next(
        (a for a in Billing.get_payment_accounts(include_inactive=False, db=db) if a.id == form_data.payment_account_id),
        None,
    )
    if not account:
        raise HTTPException(status_code=404, detail="Payment account not found")

    row = Billing.create_topup_request(
        user_id=user.id,
        api_key_id=form_data.api_key_id,
        payment_account_id=form_data.payment_account_id,
        amount=form_data.amount,
        currency=form_data.currency,
        tx_ref=form_data.tx_ref,
        note=form_data.note,
        db=db,
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create top-up request")

    Billing.log_audit(
        actor_id=user.id,
        action="topup.create",
        target_type="topup_request",
        target_id=row.id,
        details={"amount": row.amount, "currency": row.currency},
        db=db,
    )

    # --- Email notifications ---
    if getattr(request.app.state.config, "ENABLE_BILLING_EMAILS", False):
        try:
            # Notify user
            if user.email:
                notify_topup_submitted(
                    app_config=request.app.state.config,
                    user_email=user.email,
                    user_name=user.name or user.email,
                    amount=float(form_data.amount),
                    currency=form_data.currency or "USD",
                    tx_ref=form_data.tx_ref or "",
                    topup_id=row.id,
                )
            # Notify admins
            from open_webui.env import WEBUI_ADMIN_EMAIL
            if WEBUI_ADMIN_EMAIL:
                notify_admin_new_topup(
                    app_config=request.app.state.config,
                    admin_email=WEBUI_ADMIN_EMAIL,
                    user_name=user.name or user.email,
                    user_email=user.email or "",
                    amount=float(form_data.amount),
                    currency=form_data.currency or "USD",
                    topup_id=row.id,
                )
        except Exception as e:
            log.warning(f"Failed to send topup submission email: {e}")

    if bool(request.app.state.config.BILLING_AUTO_APPROVE_TOPUPS):
        credits = max(1, int(float(form_data.amount) * 100))
        _finalize_topup_approval(
            request_id=row.id,
            credits=credits,
            reviewed_by="system:auto",
            reviewed_note="Auto-approved by billing setting",
            actor_id="system:auto",
            actor_action="topup.auto_approve",
            actor_details={"reason": "billing.auto_approve_topups"},
            db=db,
            app_config=request.app.state.config,
        )
        row = Billing.get_topup_request_by_id(row.id, db=db)

    return row


@router.get("/me/topups")
async def get_my_topups(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    return Billing.get_topup_requests(user_id=user.id, db=db)


@router.get("/me/invoices")
async def get_my_invoices(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    return Billing.get_invoices(user_id=user.id, db=db)


@router.get("/me/invoices/{invoice_id}")
async def get_my_invoice_detail(
    invoice_id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    invoice = Billing.get_invoice_by_id(invoice_id, db=db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return invoice


@router.post("/webhooks/payment/{provider}")
async def payment_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_session),
    x_billing_webhook_secret: Optional[str] = Header(default=None),
):
    from open_webui.utils.webhooks import (
        verify_stripe,
        verify_vnpay,
        verify_momo,
        verify_generic,
        WebhookPayload,
    )

    body_bytes = await request.body()

    # ---- Provider-specific verification ----
    if provider == "stripe":
        sig_header = request.headers.get("stripe-signature", "")
        # Load Stripe secret from env or payment account metadata
        stripe_secret = _get_provider_secret(provider, db)
        wh = verify_stripe(body_bytes, sig_header, stripe_secret)
        if not wh.verified:
            raise HTTPException(status_code=403, detail=f"Stripe verification failed: {wh.error}")

        # For Stripe, the tx_ref is the payment intent or session ID
        # We need to find the topup by tx_ref
        form_data = _stripe_to_form(wh)

    elif provider == "vnpay":
        params = dict(request.query_params)
        vnpay_secret = _get_provider_secret(provider, db)
        wh = verify_vnpay(params, vnpay_secret)
        if not wh.verified:
            raise HTTPException(status_code=403, detail=f"VNPay verification failed: {wh.error}")
        form_data = _vnpay_to_form(wh)

    elif provider == "momo":
        body_json = json.loads(body_bytes) if body_bytes else {}
        momo_secret = _get_provider_secret(provider, db)
        wh = verify_momo(body_json, momo_secret)
        if not wh.verified:
            raise HTTPException(status_code=403, detail=f"MoMo verification failed: {wh.error}")
        form_data = _momo_to_form(wh)

    else:
        # Generic webhook — use form body + header secret
        try:
            body_json = json.loads(body_bytes) if body_bytes else {}
            form_data = PaymentWebhookForm(**body_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")

        # Verify below using payment account secret (original behavior)
        wh = None

    # ---- Process the topup ----
    if form_data.status.lower() not in {"paid", "success", "approved"}:
        return {"ok": True, "skipped": True, "reason": "payment_not_finalized"}

    topup = Billing.get_topup_request_by_id(form_data.topup_request_id, db=db)
    if not topup:
        raise HTTPException(status_code=404, detail="Top-up request not found")

    if topup.status == "approved":
        invoice = Billing.get_invoice_by_topup_request_id(topup.id, db=db)
        return {"ok": True, "idempotent": True, "invoice_id": invoice.id if invoice else None}

    if topup.status != "pending":
        raise HTTPException(status_code=400, detail="Top-up request is not pending")

    # For generic provider, verify via payment account webhook_secret
    if wh is None:
        account = Billing.get_payment_account_by_id(topup.payment_account_id, db=db)
        if not account:
            raise HTTPException(status_code=404, detail="Payment account not found")

        acct_metadata = account.metadata if isinstance(account.metadata, dict) else {}
        expected_secret = acct_metadata.get("webhook_secret")
        generic_result = verify_generic(x_billing_webhook_secret, expected_secret or "")
        if not generic_result.verified:
            raise HTTPException(status_code=403, detail=generic_result.error)

    api_key = Users.get_api_key_record_by_id(topup.api_key_id, db=db)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key_data = api_key.data if isinstance(api_key.data, dict) else {}
    amount = float(form_data.amount) if form_data.amount is not None else float(topup.amount)
    credits = int(form_data.credits) if form_data.credits is not None else max(1, int(amount * 100))

    api_key_data["credits_remaining"] = int(api_key_data.get("credits_remaining", 0)) + credits
    api_key_data["last_topup_provider"] = provider
    api_key_data["last_topup_tx_ref"] = form_data.tx_ref or topup.tx_ref

    updated_key = Users.update_api_key_by_id(api_key.id, {"data": api_key_data}, db=db)
    if not updated_key:
        raise HTTPException(status_code=500, detail="Failed to update API key credits")

    reviewed = Billing.update_topup_request_status(
        topup.id,
        status="approved",
        reviewed_by=f"webhook:{provider}",
        reviewed_note=form_data.note or "Auto-approved by payment webhook",
        db=db,
    )

    invoice = Billing.create_invoice(
        user_id=topup.user_id,
        api_key_id=topup.api_key_id,
        topup_request_id=topup.id,
        amount=amount,
        currency=form_data.currency or topup.currency,
        credits=credits,
        data={
            "provider": provider,
            "tx_ref": form_data.tx_ref or topup.tx_ref,
            "webhook_ip": request.client.host if request.client else None,
        },
        db=db,
    )

    Billing.log_audit(
        actor_id=f"webhook:{provider}",
        action="topup.approve.webhook",
        target_type="topup_request",
        target_id=topup.id,
        details={"invoice_id": invoice.id if invoice else None, "credits": credits},
        db=db,
    )

    return {
        "ok": True,
        "topup": reviewed,
        "invoice": invoice,
        "api_key": _build_console_payload(updated_key),
    }


def _get_provider_secret(provider: str, db: Session) -> str:
    """
    Get the webhook/hash secret for a given payment provider.
    Looks up payment accounts with matching provider name.
    """
    accounts = Billing.get_payment_accounts(db=db)
    for acct in accounts:
        if acct.provider.lower() == provider.lower():
            meta = acct.metadata if isinstance(acct.metadata, dict) else {}
            return meta.get("webhook_secret", meta.get("hash_secret", meta.get("secret_key", "")))
    return ""


def _stripe_to_form(wh) -> PaymentWebhookForm:
    """Convert Stripe webhook payload to internal form."""
    raw = wh.raw or {}
    data_obj = raw.get("data", {}).get("object", {})
    # Try to find topup_request_id in metadata
    mdata = data_obj.get("metadata", {})
    return PaymentWebhookForm(
        topup_request_id=mdata.get("topup_request_id", data_obj.get("client_reference_id", "")),
        status="paid" if wh.is_paid else wh.status,
        tx_ref=wh.tx_ref,
        amount=wh.amount,
        currency=wh.currency,
    )


def _vnpay_to_form(wh) -> PaymentWebhookForm:
    """Convert VNPay webhook payload to internal form."""
    raw = wh.raw or {}
    # VNPay uses vnp_OrderInfo or vnp_TxnRef as reference; topup_request_id expected in vnp_OrderInfo
    order_info = raw.get("vnp_OrderInfo", "")
    return PaymentWebhookForm(
        topup_request_id=order_info if order_info else raw.get("vnp_TxnRef", ""),
        status="paid" if wh.is_paid else wh.status,
        tx_ref=wh.tx_ref,
        amount=wh.amount,
        currency=wh.currency,
    )


def _momo_to_form(wh) -> PaymentWebhookForm:
    """Convert MoMo webhook payload to internal form."""
    raw = wh.raw or {}
    # MoMo: orderId is the topup_request_id, or in extraData
    extra = raw.get("extraData", "")
    order_id = raw.get("orderId", "")
    return PaymentWebhookForm(
        topup_request_id=order_id if order_id else extra,
        status="paid" if wh.is_paid else wh.status,
        tx_ref=wh.tx_ref,
        amount=wh.amount,
        currency=wh.currency,
    )
