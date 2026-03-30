"""
Billing utilities – post-response cost calculation & usage logging.

Called from the response middleware after an LLM response completes.
If admin has set up model pricing, token-based cost is applied;
otherwise the existing 1-credit-per-request model is used.
"""

import logging
import time
from typing import Any, Optional

from open_webui.models.billing import Billing
from open_webui.models.users import Users

log = logging.getLogger(__name__)


def finalize_billing(
    user_id: str,
    api_key: str,
    model: str,
    usage: Optional[dict],
    endpoint: Optional[str] = None,
    request_metadata: Optional[dict] = None,
) -> None:
    """
    Post-response billing hook.

    1. Resolve model pricing (if configured by admin).
    2. Calculate actual cost from token counts.
    3. Adjust API key credits (the pre-auth already deducted 1 credit).
    4. Log usage to the usage_log table.

    Runs fire-and-forget; errors are logged but never raised.
    """
    try:
        # ------------------------------------------------------------------
        # 1. Load the API key record
        # ------------------------------------------------------------------
        key_record = Users.get_api_key_record_by_key(api_key)
        if not key_record:
            return  # key was somehow deleted mid-request; nothing to do

        api_key_id = key_record.id
        metadata: dict[str, Any] = (
            key_record.data if isinstance(key_record.data, dict) else {}
        )

        # ------------------------------------------------------------------
        # 2. Parse token counts from usage
        # ------------------------------------------------------------------
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if usage and isinstance(usage, dict):
            prompt_tokens = int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("output_tokens", 0) or usage.get("completion_tokens", 0) or 0)
            total_tokens = int(usage.get("total_tokens", 0) or (prompt_tokens + completion_tokens))

        # ------------------------------------------------------------------
        # 3. Resolve pricing & calculate cost
        # ------------------------------------------------------------------
        pricing = Billing.resolve_model_pricing(model)

        input_cost = 0.0
        output_cost = 0.0
        per_req_cost = 0.0
        total_cost = 0.0
        credits_to_adjust = 0  # adjustment relative to the 1 credit pre-deducted

        if pricing:
            input_cost = round((prompt_tokens / 1000.0) * pricing.input_cost_per_1k_tokens, 8)
            output_cost = round((completion_tokens / 1000.0) * pricing.output_cost_per_1k_tokens, 8)
            per_req_cost = pricing.per_request_cost
            total_cost = round(input_cost + output_cost + per_req_cost, 8)

            # Convert USD cost → credits.  1 credit ≈ 1 request unit.
            # If model pricing is active the admin decides a credit_value_usd.
            # Default: 1 credit = per_request_cost of the cheapest plan or $0.001
            credit_value = float(metadata.get("credit_value_usd", 0))
            if credit_value <= 0:
                credit_value = 0.001  # fallback: 1 credit = $0.001

            actual_credits = max(1, int(total_cost / credit_value + 0.5))

            # consume_api_key_credit already deducted 1 credit.
            # If actual cost requires more → deduct extra.
            # If actual cost requires less → do nothing (minimum 1 credit/req).
            credits_to_adjust = actual_credits - 1  # positive = deduct more

            if credits_to_adjust > 0:
                current = int(metadata.get("credits_remaining", 0))
                metadata["credits_remaining"] = max(0, current - credits_to_adjust)
                Users.update_api_key_by_id(key_record.id, {"data": metadata})
        else:
            # No model pricing → flat 1 credit per request (already deducted)
            total_cost = 0.0

        actual_credits_deducted = 1 + max(0, credits_to_adjust)

        # ------------------------------------------------------------------
        # 4. Log to usage_log table
        # ------------------------------------------------------------------
        Billing.create_usage_log(
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
            credits_deducted=actual_credits_deducted,
            currency=pricing.currency if pricing else "VND",
            request_metadata=request_metadata,
        )

    except Exception as e:
        log.warning(f"[billing] finalize_billing error: {e}")
