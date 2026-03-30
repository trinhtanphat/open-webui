"""
Payment gateway webhook verification utilities.

Supports: Stripe, VNPay, MoMo + generic.
Each verifier validates the request signature and extracts normalized payment data.
"""

import hashlib
import hmac
import json
import logging
import urllib.parse
from typing import Any, Optional

log = logging.getLogger(__name__)


class WebhookPayload:
    """Normalized result from webhook verification."""

    def __init__(
        self,
        verified: bool,
        tx_ref: str = "",
        amount: float = 0,
        currency: str = "VND",
        status: str = "",
        raw: Optional[dict] = None,
        error: str = "",
    ):
        self.verified = verified
        self.tx_ref = tx_ref
        self.amount = amount
        self.currency = currency
        self.status = status
        self.raw = raw or {}
        self.error = error

    @property
    def is_paid(self) -> bool:
        return self.status.lower() in {"paid", "success", "approved", "complete", "completed"}


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

def verify_stripe(
    payload_body: bytes,
    signature_header: str,
    webhook_secret: str,
) -> WebhookPayload:
    """
    Verify a Stripe webhook event using the Stripe-Signature header.
    Uses HMAC-SHA256 (v1 scheme).
    """
    try:
        if not signature_header or not webhook_secret:
            return WebhookPayload(verified=False, error="Missing signature or secret")

        # Parse Stripe signature header: t=<timestamp>,v1=<sig>,v0=<sig>
        elements = {}
        for item in signature_header.split(","):
            key, _, value = item.strip().partition("=")
            elements.setdefault(key, []).append(value)

        timestamp = elements.get("t", [None])[0]
        signatures = elements.get("v1", [])

        if not timestamp or not signatures:
            return WebhookPayload(verified=False, error="Invalid Stripe-Signature format")

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload_body.decode('utf-8')}"
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not any(hmac.compare_digest(expected, sig) for sig in signatures):
            return WebhookPayload(verified=False, error="Signature mismatch")

        event = json.loads(payload_body)
        event_type = event.get("type", "")
        data_obj = event.get("data", {}).get("object", {})

        # We mainly care about checkout.session.completed or payment_intent.succeeded
        status = "paid" if event_type in (
            "checkout.session.completed",
            "payment_intent.succeeded",
            "invoice.paid",
        ) else event_type

        return WebhookPayload(
            verified=True,
            tx_ref=data_obj.get("id", data_obj.get("payment_intent", "")),
            amount=float(data_obj.get("amount_total", data_obj.get("amount", 0))) / 100,
            currency=(data_obj.get("currency", "vnd")).upper(),
            status=status,
            raw=event,
        )
    except Exception as e:
        log.error(f"Stripe webhook verification failed: {e}")
        return WebhookPayload(verified=False, error=str(e))


# ---------------------------------------------------------------------------
# VNPay
# ---------------------------------------------------------------------------

def verify_vnpay(
    query_params: dict[str, str],
    hash_secret: str,
) -> WebhookPayload:
    """
    Verify VNPay IPN/return URL by checking vnp_SecureHash.
    VNPay uses HMAC-SHA512 over sorted query params (excluding vnp_SecureHash, vnp_SecureHashType).
    """
    try:
        if not hash_secret:
            return WebhookPayload(verified=False, error="Missing VNPay hash secret")

        secure_hash = query_params.get("vnp_SecureHash", "")
        if not secure_hash:
            return WebhookPayload(verified=False, error="Missing vnp_SecureHash")

        # Build hash data: sorted params excluding hash fields
        filtered = {
            k: v for k, v in query_params.items()
            if k not in ("vnp_SecureHash", "vnp_SecureHashType")
        }
        sorted_params = sorted(filtered.items())
        hash_data = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params)

        expected = hmac.new(
            hash_secret.encode("utf-8"),
            hash_data.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()

        if not hmac.compare_digest(expected.lower(), secure_hash.lower()):
            return WebhookPayload(verified=False, error="VNPay hash mismatch")

        response_code = query_params.get("vnp_ResponseCode", "")
        status = "paid" if response_code == "00" else f"vnpay_code_{response_code}"

        return WebhookPayload(
            verified=True,
            tx_ref=query_params.get("vnp_TxnRef", ""),
            amount=float(query_params.get("vnp_Amount", 0)) / 100,  # VNPay amount is x100
            currency="VND",
            status=status,
            raw=query_params,
        )
    except Exception as e:
        log.error(f"VNPay webhook verification failed: {e}")
        return WebhookPayload(verified=False, error=str(e))


# ---------------------------------------------------------------------------
# MoMo
# ---------------------------------------------------------------------------

def verify_momo(
    body: dict[str, Any],
    secret_key: str,
) -> WebhookPayload:
    """
    Verify MoMo IPN callback by checking HMAC-SHA256 signature.
    MoMo signs: accessKey + amount + extraData + message + orderId + orderInfo +
    orderType + partnerCode + payType + requestId + responseTime + resultCode + transId
    """
    try:
        if not secret_key:
            return WebhookPayload(verified=False, error="Missing MoMo secret key")

        signature = body.get("signature", "")
        if not signature:
            return WebhookPayload(verified=False, error="Missing MoMo signature")

        # Build raw data string in MoMo's documented order
        fields = [
            "accessKey", "amount", "extraData", "message", "orderId",
            "orderInfo", "orderType", "partnerCode", "payType",
            "requestId", "responseTime", "resultCode", "transId",
        ]
        raw_data = "&".join(f"{f}={body.get(f, '')}" for f in fields)

        expected = hmac.new(
            secret_key.encode("utf-8"),
            raw_data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected.lower(), signature.lower()):
            return WebhookPayload(verified=False, error="MoMo signature mismatch")

        result_code = str(body.get("resultCode", ""))
        status = "paid" if result_code == "0" else f"momo_code_{result_code}"

        return WebhookPayload(
            verified=True,
            tx_ref=body.get("orderId", body.get("transId", "")),
            amount=float(body.get("amount", 0)),
            currency="VND",
            status=status,
            raw=body,
        )
    except Exception as e:
        log.error(f"MoMo webhook verification failed: {e}")
        return WebhookPayload(verified=False, error=str(e))


# ---------------------------------------------------------------------------
# Generic (header-secret based)
# ---------------------------------------------------------------------------

def verify_generic(
    webhook_secret_header: Optional[str],
    expected_secret: str,
) -> WebhookPayload:
    """Simple secret-comparison verification for generic webhooks."""
    if not expected_secret:
        return WebhookPayload(verified=False, error="No webhook secret configured")
    if not webhook_secret_header or webhook_secret_header != expected_secret:
        return WebhookPayload(verified=False, error="Invalid webhook secret")
    return WebhookPayload(verified=True, status="paid")
