import fnmatch
import time
import uuid
from typing import Any, Optional
from collections import defaultdict
import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import BigInteger, Boolean, Column, Float, JSON, Text
from sqlalchemy.orm import Session

from open_webui.internal.db import Base, get_db_context


# ---------------------------------------------------------------------------
# Model Pricing – admin-configurable per-model cost
# ---------------------------------------------------------------------------
class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id = Column(Text, primary_key=True, unique=True)
    model_id = Column(Text, nullable=False, unique=True)  # exact name or glob "gpt-4*"
    display_name = Column(Text, nullable=True)
    input_cost_per_1k_tokens = Column(Float, nullable=False, default=0.0)
    output_cost_per_1k_tokens = Column(Float, nullable=False, default=0.0)
    per_request_cost = Column(Float, nullable=False, default=0.0)
    currency = Column(Text, nullable=False, default="USD")
    is_active = Column(Text, nullable=False, default="true")
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


# ---------------------------------------------------------------------------
# Usage Log – one row per API request with token + cost breakdown
# ---------------------------------------------------------------------------
class UsageLog(Base):
    __tablename__ = "usage_log"

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text, nullable=False)
    api_key_id = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    endpoint = Column(Text, nullable=True)
    prompt_tokens = Column(BigInteger, nullable=False, default=0)
    completion_tokens = Column(BigInteger, nullable=False, default=0)
    total_tokens = Column(BigInteger, nullable=False, default=0)
    input_cost = Column(Float, nullable=False, default=0.0)
    output_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    credits_deducted = Column(BigInteger, nullable=False, default=0)
    currency = Column(Text, nullable=False, default="USD")
    request_metadata = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)


class BillingPaymentAccount(Base):
    __tablename__ = "billing_payment_account"

    id = Column(Text, primary_key=True, unique=True)
    provider = Column(Text, nullable=False)
    account_name = Column(Text, nullable=False)
    account_number = Column(Text, nullable=False)
    qr_code_url = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    billing_metadata = Column("metadata", JSON, nullable=True)
    is_active = Column(Text, nullable=False, default="true")
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class BillingTopupRequest(Base):
    __tablename__ = "billing_topup_request"

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text, nullable=False)
    api_key_id = Column(Text, nullable=False)
    payment_account_id = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    tx_ref = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="pending")
    reviewed_by = Column(Text, nullable=True)
    reviewed_note = Column(Text, nullable=True)
    reviewed_at = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class BillingInvoice(Base):
    __tablename__ = "billing_invoice"

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text, nullable=False)
    api_key_id = Column(Text, nullable=False)
    topup_request_id = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    credits = Column(BigInteger, nullable=False)
    status = Column(Text, nullable=False, default="paid")
    data = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class BillingAuditLog(Base):
    __tablename__ = "billing_audit_log"

    id = Column(Text, primary_key=True, unique=True)
    actor_id = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    target_type = Column(Text, nullable=False)
    target_id = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)


class BillingPaymentAccountModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    provider: str
    account_name: str
    account_number: str
    qr_code_url: Optional[str] = None
    instructions: Optional[str] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias="billing_metadata",
        serialization_alias="metadata",
    )
    is_active: str = "true"
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: int
    updated_at: int


class BillingTopupRequestModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    api_key_id: str
    payment_account_id: str
    amount: float
    currency: str = "USD"
    tx_ref: Optional[str] = None
    note: Optional[str] = None
    status: str = "pending"
    reviewed_by: Optional[str] = None
    reviewed_note: Optional[str] = None
    reviewed_at: Optional[int] = None
    created_at: int
    updated_at: int


class BillingInvoiceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    api_key_id: str
    topup_request_id: Optional[str] = None
    amount: float
    currency: str = "USD"
    credits: int
    status: str = "paid"
    data: Optional[dict] = None
    created_at: int
    updated_at: int


class BillingAuditLogModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    details: Optional[dict] = None
    created_at: int


# ---------------------------------------------------------------------------
# Pydantic models for new tables
# ---------------------------------------------------------------------------
class ModelPricingModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_id: str
    display_name: Optional[str] = None
    input_cost_per_1k_tokens: float = 0.0
    output_cost_per_1k_tokens: float = 0.0
    per_request_cost: float = 0.0
    currency: str = "USD"
    is_active: str = "true"
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: int
    updated_at: int


class UsageLogModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    api_key_id: str
    model: str
    endpoint: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    credits_deducted: int = 0
    currency: str = "USD"
    request_metadata: Optional[dict] = None
    created_at: int


class BillingTable:
    def create_payment_account(
        self,
        provider: str,
        account_name: str,
        account_number: str,
        qr_code_url: Optional[str],
        instructions: Optional[str],
        metadata: Optional[dict],
        actor_id: str,
        db: Optional[Session] = None,
    ) -> Optional[BillingPaymentAccountModel]:
        try:
            with get_db_context(db) as db:
                now = int(time.time())
                record = BillingPaymentAccount(
                    id=str(uuid.uuid4()),
                    provider=provider,
                    account_name=account_name,
                    account_number=account_number,
                    qr_code_url=qr_code_url,
                    instructions=instructions,
                    billing_metadata=metadata,
                    is_active="true",
                    created_by=actor_id,
                    updated_by=actor_id,
                    created_at=now,
                    updated_at=now,
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                return BillingPaymentAccountModel.model_validate(record)
        except Exception:
            return None

    def get_payment_accounts(
        self,
        include_inactive: bool = False,
        db: Optional[Session] = None,
    ) -> list[BillingPaymentAccountModel]:
        with get_db_context(db) as db:
            query = db.query(BillingPaymentAccount)
            if not include_inactive:
                query = query.filter(BillingPaymentAccount.is_active == "true")
            rows = query.order_by(BillingPaymentAccount.created_at.desc()).all()
            return [BillingPaymentAccountModel.model_validate(row) for row in rows]

    def get_payment_account_by_id(
        self,
        account_id: str,
        db: Optional[Session] = None,
    ) -> Optional[BillingPaymentAccountModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(BillingPaymentAccount).filter_by(id=account_id).first()
                return BillingPaymentAccountModel.model_validate(row) if row else None
        except Exception:
            return None

    def update_payment_account(
        self,
        account_id: str,
        updated: dict,
        actor_id: str,
        db: Optional[Session] = None,
    ) -> Optional[BillingPaymentAccountModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(BillingPaymentAccount).filter_by(id=account_id).first()
                if not row:
                    return None
                for key, value in updated.items():
                    if key == "metadata":
                        key = "billing_metadata"
                    setattr(row, key, value)
                row.updated_by = actor_id
                row.updated_at = int(time.time())
                db.commit()
                db.refresh(row)
                return BillingPaymentAccountModel.model_validate(row)
        except Exception:
            return None

    def create_topup_request(
        self,
        user_id: str,
        api_key_id: str,
        payment_account_id: str,
        amount: float,
        currency: str,
        tx_ref: Optional[str],
        note: Optional[str],
        db: Optional[Session] = None,
    ) -> Optional[BillingTopupRequestModel]:
        try:
            with get_db_context(db) as db:
                now = int(time.time())
                row = BillingTopupRequest(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    api_key_id=api_key_id,
                    payment_account_id=payment_account_id,
                    amount=amount,
                    currency=currency,
                    tx_ref=tx_ref,
                    note=note,
                    status="pending",
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return BillingTopupRequestModel.model_validate(row)
        except Exception:
            return None

    def get_topup_requests(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> list[BillingTopupRequestModel]:
        with get_db_context(db) as db:
            query = db.query(BillingTopupRequest)
            if user_id:
                query = query.filter(BillingTopupRequest.user_id == user_id)
            if status:
                query = query.filter(BillingTopupRequest.status == status)
            rows = query.order_by(BillingTopupRequest.created_at.desc()).all()
            return [BillingTopupRequestModel.model_validate(row) for row in rows]

    def get_topup_request_by_id(
        self, request_id: str, db: Optional[Session] = None
    ) -> Optional[BillingTopupRequestModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(BillingTopupRequest).filter_by(id=request_id).first()
                return BillingTopupRequestModel.model_validate(row) if row else None
        except Exception:
            return None

    def update_topup_request_status(
        self,
        request_id: str,
        status: str,
        reviewed_by: str,
        reviewed_note: Optional[str],
        db: Optional[Session] = None,
    ) -> Optional[BillingTopupRequestModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(BillingTopupRequest).filter_by(id=request_id).first()
                if not row:
                    return None
                row.status = status
                row.reviewed_by = reviewed_by
                row.reviewed_note = reviewed_note
                row.reviewed_at = int(time.time())
                row.updated_at = int(time.time())
                db.commit()
                db.refresh(row)
                return BillingTopupRequestModel.model_validate(row)
        except Exception:
            return None

    def create_invoice(
        self,
        user_id: str,
        api_key_id: str,
        topup_request_id: Optional[str],
        amount: float,
        currency: str,
        credits: int,
        data: Optional[dict],
        db: Optional[Session] = None,
    ) -> Optional[BillingInvoiceModel]:
        try:
            with get_db_context(db) as db:
                now = int(time.time())
                row = BillingInvoice(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    api_key_id=api_key_id,
                    topup_request_id=topup_request_id,
                    amount=amount,
                    currency=currency,
                    credits=credits,
                    status="paid",
                    data=data,
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return BillingInvoiceModel.model_validate(row)
        except Exception:
            return None

    def get_invoices(
        self, user_id: Optional[str] = None, db: Optional[Session] = None
    ) -> list[BillingInvoiceModel]:
        with get_db_context(db) as db:
            query = db.query(BillingInvoice)
            if user_id:
                query = query.filter(BillingInvoice.user_id == user_id)
            rows = query.order_by(BillingInvoice.created_at.desc()).all()
            return [BillingInvoiceModel.model_validate(row) for row in rows]

    def get_invoice_by_id(
        self,
        invoice_id: str,
        db: Optional[Session] = None,
    ) -> Optional[BillingInvoiceModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(BillingInvoice).filter_by(id=invoice_id).first()
                return BillingInvoiceModel.model_validate(row) if row else None
        except Exception:
            return None

    def get_invoice_by_topup_request_id(
        self,
        topup_request_id: str,
        db: Optional[Session] = None,
    ) -> Optional[BillingInvoiceModel]:
        try:
            with get_db_context(db) as db:
                row = (
                    db.query(BillingInvoice)
                    .filter_by(topup_request_id=topup_request_id)
                    .first()
                )
                return BillingInvoiceModel.model_validate(row) if row else None
        except Exception:
            return None

    def get_daily_revenue(
        self,
        days: int = 30,
        db: Optional[Session] = None,
    ) -> list[dict]:
        with get_db_context(db) as db:
            rows = db.query(BillingInvoice).filter(BillingInvoice.status == "paid").all()

            day_totals = defaultdict(lambda: {"revenue": 0.0, "credits": 0, "invoices": 0})
            now = int(time.time())
            start_ts = now - max(1, days) * 86400

            for row in rows:
                if row.created_at < start_ts:
                    continue

                day = datetime.datetime.utcfromtimestamp(row.created_at).strftime("%Y-%m-%d")
                day_totals[day]["revenue"] += float(row.amount)
                day_totals[day]["credits"] += int(row.credits)
                day_totals[day]["invoices"] += 1

            result = []
            for day in sorted(day_totals.keys()):
                result.append({"date": day, **day_totals[day]})

            return result

    def log_audit(
        self,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        details: Optional[dict],
        db: Optional[Session] = None,
    ) -> Optional[BillingAuditLogModel]:
        try:
            with get_db_context(db) as db:
                row = BillingAuditLog(
                    id=str(uuid.uuid4()),
                    actor_id=actor_id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    details=details,
                    created_at=int(time.time()),
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return BillingAuditLogModel.model_validate(row)
        except Exception:
            return None

    def get_audit_logs(self, limit: int = 100, db: Optional[Session] = None) -> list[BillingAuditLogModel]:
        with get_db_context(db) as db:
            rows = (
                db.query(BillingAuditLog)
                .order_by(BillingAuditLog.created_at.desc())
                .limit(max(1, min(limit, 500)))
                .all()
            )
            return [BillingAuditLogModel.model_validate(row) for row in rows]

    # -----------------------------------------------------------------------
    # Model Pricing CRUD
    # -----------------------------------------------------------------------
    def create_model_pricing(
        self,
        model_id: str,
        display_name: Optional[str],
        input_cost_per_1k_tokens: float,
        output_cost_per_1k_tokens: float,
        per_request_cost: float,
        currency: str,
        actor_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ModelPricingModel]:
        try:
            with get_db_context(db) as db:
                now = int(time.time())
                row = ModelPricing(
                    id=str(uuid.uuid4()),
                    model_id=model_id,
                    display_name=display_name or model_id,
                    input_cost_per_1k_tokens=input_cost_per_1k_tokens,
                    output_cost_per_1k_tokens=output_cost_per_1k_tokens,
                    per_request_cost=per_request_cost,
                    currency=currency,
                    is_active="true",
                    created_by=actor_id,
                    updated_by=actor_id,
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return ModelPricingModel.model_validate(row)
        except Exception:
            return None

    def get_model_pricings(
        self,
        include_inactive: bool = False,
        db: Optional[Session] = None,
    ) -> list[ModelPricingModel]:
        with get_db_context(db) as db:
            query = db.query(ModelPricing)
            if not include_inactive:
                query = query.filter(ModelPricing.is_active == "true")
            rows = query.order_by(ModelPricing.model_id.asc()).all()
            return [ModelPricingModel.model_validate(row) for row in rows]

    def get_model_pricing_by_id(
        self, pricing_id: str, db: Optional[Session] = None
    ) -> Optional[ModelPricingModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(ModelPricing).filter_by(id=pricing_id).first()
                return ModelPricingModel.model_validate(row) if row else None
        except Exception:
            return None

    def update_model_pricing(
        self,
        pricing_id: str,
        updated: dict,
        actor_id: str,
        db: Optional[Session] = None,
    ) -> Optional[ModelPricingModel]:
        try:
            with get_db_context(db) as db:
                row = db.query(ModelPricing).filter_by(id=pricing_id).first()
                if not row:
                    return None
                for key, value in updated.items():
                    setattr(row, key, value)
                row.updated_by = actor_id
                row.updated_at = int(time.time())
                db.commit()
                db.refresh(row)
                return ModelPricingModel.model_validate(row)
        except Exception:
            return None

    def delete_model_pricing(
        self, pricing_id: str, db: Optional[Session] = None
    ) -> bool:
        try:
            with get_db_context(db) as db:
                row = db.query(ModelPricing).filter_by(id=pricing_id).first()
                if not row:
                    return False
                db.delete(row)
                db.commit()
                return True
        except Exception:
            return False

    def resolve_model_pricing(
        self, model_name: str, db: Optional[Session] = None
    ) -> Optional[ModelPricingModel]:
        """Find best-matching pricing for a model.
        Tries exact match first, then glob patterns (e.g. 'gpt-4*')."""
        with get_db_context(db) as db:
            rows = (
                db.query(ModelPricing)
                .filter(ModelPricing.is_active == "true")
                .all()
            )
            # exact match first
            for row in rows:
                if row.model_id == model_name:
                    return ModelPricingModel.model_validate(row)
            # glob / fnmatch
            for row in rows:
                if fnmatch.fnmatch(model_name.lower(), row.model_id.lower()):
                    return ModelPricingModel.model_validate(row)
            return None

    # -----------------------------------------------------------------------
    # Usage Log CRUD
    # -----------------------------------------------------------------------
    def create_usage_log(
        self,
        user_id: str,
        api_key_id: str,
        model: str,
        endpoint: Optional[str],
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        input_cost: float,
        output_cost: float,
        total_cost: float,
        credits_deducted: int,
        currency: str = "USD",
        request_metadata: Optional[dict] = None,
        db: Optional[Session] = None,
    ) -> Optional[UsageLogModel]:
        try:
            with get_db_context(db) as db:
                row = UsageLog(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    api_key_id=api_key_id,
                    model=model,
                    endpoint=endpoint,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    total_cost=total_cost,
                    credits_deducted=credits_deducted,
                    currency=currency,
                    request_metadata=request_metadata,
                    created_at=int(time.time()),
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return UsageLogModel.model_validate(row)
        except Exception:
            return None

    def get_usage_logs(
        self,
        user_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        model: Optional[str] = None,
        days: int = 30,
        limit: int = 500,
        db: Optional[Session] = None,
    ) -> list[UsageLogModel]:
        with get_db_context(db) as db:
            query = db.query(UsageLog)
            if user_id:
                query = query.filter(UsageLog.user_id == user_id)
            if api_key_id:
                query = query.filter(UsageLog.api_key_id == api_key_id)
            if model:
                query = query.filter(UsageLog.model == model)

            start_ts = int(time.time()) - max(1, days) * 86400
            query = query.filter(UsageLog.created_at >= start_ts)
            rows = (
                query.order_by(UsageLog.created_at.desc())
                .limit(max(1, min(limit, 5000)))
                .all()
            )
            return [UsageLogModel.model_validate(row) for row in rows]

    def get_usage_daily_summary(
        self,
        user_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        days: int = 30,
        db: Optional[Session] = None,
    ) -> list[dict]:
        """Aggregate usage by day → {date, requests, prompt_tokens, completion_tokens, total_tokens, total_cost}"""
        with get_db_context(db) as db:
            query = db.query(UsageLog)
            if user_id:
                query = query.filter(UsageLog.user_id == user_id)
            if api_key_id:
                query = query.filter(UsageLog.api_key_id == api_key_id)

            start_ts = int(time.time()) - max(1, days) * 86400
            query = query.filter(UsageLog.created_at >= start_ts)
            rows = query.all()

            day_totals: dict[str, dict[str, Any]] = defaultdict(
                lambda: {
                    "requests": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }
            )
            for row in rows:
                day = datetime.datetime.utcfromtimestamp(row.created_at).strftime("%Y-%m-%d")
                day_totals[day]["requests"] += 1
                day_totals[day]["prompt_tokens"] += int(row.prompt_tokens)
                day_totals[day]["completion_tokens"] += int(row.completion_tokens)
                day_totals[day]["total_tokens"] += int(row.total_tokens)
                day_totals[day]["total_cost"] += float(row.total_cost)

            result = []
            for day in sorted(day_totals.keys()):
                result.append({"date": day, **day_totals[day]})
            return result

    def get_usage_by_model_summary(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
        db: Optional[Session] = None,
    ) -> list[dict]:
        """Aggregate usage by model → {model, requests, total_tokens, total_cost}"""
        with get_db_context(db) as db:
            query = db.query(UsageLog)
            if user_id:
                query = query.filter(UsageLog.user_id == user_id)

            start_ts = int(time.time()) - max(1, days) * 86400
            query = query.filter(UsageLog.created_at >= start_ts)
            rows = query.all()

            model_totals: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"requests": 0, "total_tokens": 0, "total_cost": 0.0}
            )
            for row in rows:
                model_totals[row.model]["requests"] += 1
                model_totals[row.model]["total_tokens"] += int(row.total_tokens)
                model_totals[row.model]["total_cost"] += float(row.total_cost)

            result = []
            for model_name in sorted(model_totals.keys()):
                result.append({"model": model_name, **model_totals[model_name]})
            return result


Billing = BillingTable()
