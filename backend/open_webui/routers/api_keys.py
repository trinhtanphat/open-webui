import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from open_webui.internal.db import get_session
from open_webui.models.billing import Billing
from open_webui.models.users import Users
from open_webui.utils.auth import create_api_key, get_admin_user, get_verified_user

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


class PaymentWebhookForm(BaseModel):
    topup_request_id: str
    status: str
    payment_account_id: Optional[str] = None
    tx_ref: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    credits: Optional[int] = None
    note: Optional[str] = None


def _mask_key(key: str) -> str:
    if len(key) <= 10:
        return key
    return f"{key[:6]}...{key[-4:]}"


def _build_console_payload(record) -> ApiKeyConsoleResponse:
    metadata = record.data if isinstance(record.data, dict) else {}
    return ApiKeyConsoleResponse(
        id=record.id,
        user_id=record.user_id,
        key=record.key,
        key_masked=_mask_key(record.key),
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


@router.get("/me", response_model=ApiKeyConsoleResponse)
async def get_my_api_key_console(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    record = Users.get_user_api_key_record_by_id(user.id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")

    return _build_console_payload(record)


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

    return _build_console_payload(new_record)


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

    return _build_console_payload(updated)


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
    return Billing.get_topup_requests(status=status, db=db)


@router.post("/admin/topups/{request_id}/approve")
async def approve_topup_request(
    request_id: str,
    form_data: TopupReviewForm,
    user=Depends(get_admin_user),
    db: Session = Depends(get_session),
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
    metadata["credits_remaining"] = int(metadata.get("credits_remaining", 0)) + max(0, int(form_data.credits))
    metadata["updated_by_admin"] = user.id

    updated_key = Users.update_api_key_by_id(key_row.id, {"data": metadata}, db=db)
    if not updated_key:
        raise HTTPException(status_code=500, detail="Failed to add credits")

    reviewed = Billing.update_topup_request_status(
        request_id,
        status="approved",
        reviewed_by=user.id,
        reviewed_note=form_data.note,
        db=db,
    )

    invoice = Billing.create_invoice(
        user_id=request_row.user_id,
        api_key_id=request_row.api_key_id,
        topup_request_id=request_row.id,
        amount=request_row.amount,
        currency=request_row.currency,
        credits=max(0, int(form_data.credits)),
        data={"approved_by": user.id, "note": form_data.note},
        db=db,
    )

    Billing.log_audit(
        actor_id=user.id,
        action="topup.approve",
        target_type="topup_request",
        target_id=request_id,
        details={"credits": form_data.credits, "invoice_id": invoice.id if invoice else None},
        db=db,
    )

    return {
        "topup": reviewed,
        "api_key": _build_console_payload(updated_key),
        "invoice": invoice,
    }


@router.post("/admin/topups/{request_id}/reject")
async def reject_topup_request(
    request_id: str,
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

    return reviewed


@router.get("/admin/invoices")
async def get_admin_invoices(user=Depends(get_admin_user), db: Session = Depends(get_session)):
    return Billing.get_invoices(db=db)


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
    return Billing.get_audit_logs(limit=limit, db=db)


@router.get("/payment-accounts")
async def get_public_payment_accounts(user=Depends(get_verified_user), db: Session = Depends(get_session)):
    return Billing.get_payment_accounts(include_inactive=False, db=db)


@router.post("/me/topups")
async def create_my_topup_request(
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
    form_data: PaymentWebhookForm,
    request: Request,
    x_billing_webhook_secret: Optional[str] = Header(default=None),
    db: Session = Depends(get_session),
):
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

    account = Billing.get_payment_account_by_id(topup.payment_account_id, db=db)
    if not account:
        raise HTTPException(status_code=404, detail="Payment account not found")

    metadata = account.metadata if isinstance(account.metadata, dict) else {}
    expected_secret = metadata.get("webhook_secret")
    if expected_secret:
        if not x_billing_webhook_secret or x_billing_webhook_secret != expected_secret:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")
    else:
        raise HTTPException(status_code=403, detail="Webhook secret not configured for payment account")

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
