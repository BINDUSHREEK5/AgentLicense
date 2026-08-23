"""
REAL x402-protected license purchase endpoint.

Uses x402HTTPResourceServer directly (the same class the official ASGI/Flask
middleware wrappers call internally) rather than the pre-built middleware, so
that this route handler has direct, synchronous access to the genuine
ProcessSettleResult - including the real Algorand transaction id - returned
by the facilitator's /settle call, in order to persist real provenance into
the AgentLicense License/Payment records.

This is still 100% the official x402-avm SDK: same HTTPRequestContext, same
process_http_request()/process_settlement() calls, same PAYMENT-REQUIRED /
PAYMENT-SIGNATURE / PAYMENT-RESPONSE headers, same facilitator network calls.
Nothing about the protocol mechanics is reimplemented or simulated here.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Payment, PaymentStatus
from app.config import settings
from app.payments.x402_avm import (
    build_resource_server,
    build_purchase_routes,
    TIER_PRICING,
    is_configured,
)
from app.licensing.license_service import create_license

from x402.http.types import HTTPRequestContext
from x402.http.middleware.fastapi import FastAPIAdapter


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/x402",
    tags=["x402-real-payments"],
)


# Built once at import time.
# Raises a clear configuration error instead of silently falling back
# to a fake payment scheme.
_server = None
_routes = None
_init_error: str | None = None


if is_configured():
    try:
        _server = build_resource_server()
        _routes = build_purchase_routes()
    except Exception as exc:
        _init_error = str(exc)
        logger.error(
            "Failed to build real x402-avm resource server: %s",
            exc,
        )
else:
    _init_error = (
        "AVM_ADDRESS is not set in backend/.env. "
        "Real x402 purchase routes are disabled until a real "
        "Algorand receiving address is configured."
    )

    logger.warning(_init_error)


def _require_configured():
    """Ensure the real x402 server is configured."""

    if _server is None or _routes is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Real x402 payment routes are not configured on this server. "
                f"{_init_error}"
            ),
        )


@router.get("/status")
def x402_status():
    """
    Report the real configuration status of the x402 payment layer.
    """

    return {
        "configured": _server is not None,
        "error": _init_error,
        "facilitator_url": settings.x402_facilitator_url,
        "network": settings.algorand_network,
        "avm_address_set": bool(settings.avm_address),
        "tiers": {
            tier: {
                "label": cfg["label"],
                "price_usdc": (
                    int(cfg["amount_micro_usdc"]) / 1_000_000
                ),
                "usage_limit": cfg["usage_limit"],
                "commercial_use": cfg["commercial_use"],
            }
            for tier, cfg in TIER_PRICING.items()
        },
    }


@router.post("/purchase/{tier}")
async def purchase_license(
    tier: str,
    resource_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Purchase an AgentLicense license tier via a REAL x402 payment
    on Algorand TestNet or mainnet.

    Flow:

      1. No PAYMENT-SIGNATURE header:
         returns genuine HTTP 402 payment requirements.

      2. Client builds and signs a real Algorand transaction and
         retries with PAYMENT-SIGNATURE.

      3. The real x402 facilitator verifies the payment.

      4. The facilitator settles the payment.

      5. Only after successful settlement is the AgentLicense
         license created.

      6. The real Algorand transaction ID is stored as provenance.
    """

    _require_configured()

    if tier not in TIER_PRICING:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tier '{tier}'",
        )

    route_key = f"POST /x402/purchase/{tier}"

    if route_key not in _routes:
        raise HTTPException(
            status_code=500,
            detail="Route not registered",
        )

    # Build a single-route view of the server for this tier.
    from x402.http.x402_http_server import x402HTTPResourceServer

    http_server = x402HTTPResourceServer(
        _server,
        {route_key: _routes[route_key]},
    )

    try:
        http_server.initialize()

    except Exception as exc:
        logger.error(
            "x402 initialize() failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not reach the x402 facilitator to sync supported "
                f"payment schemes ({settings.x402_facilitator_url}). "
                f"Underlying error: {exc}"
            ),
        )

    adapter = FastAPIAdapter(request)

    payment_header = (
        adapter.get_header("payment-signature")
        or adapter.get_header("x-payment")
    )

    context = HTTPRequestContext(
        adapter=adapter,
        path=route_key.split(" ", 1)[1],
        method="POST",
        payment_header=payment_header,
    )

    # Process the HTTP request through the official x402 SDK.
    result = await http_server.process_http_request(context)
    logger.info("========== X402 PROCESS RESULT ==========")
    logger.info("result.type=%s", result.type)
    logger.info("result=%r", result)

    if result.type == "payment-error":
        logger.error("X402 PAYMENT ERROR RESPONSE=%r", result.response)

    logger.info("========================================")

    # Payment is required or another payment error occurred.
    if result.type == "payment-error":
        resp = result.response

        status = resp.status if resp else 402

        body = (
            resp.body
            if resp
            else {
                "error": "Payment required"
            }
        )

        headers = resp.headers if resp else {}

        return JSONResponse(
            status_code=status,
            content=body,
            headers=headers,
        )

    # We expect a verified payment at this point.
    if result.type != "payment-verified":
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected result type: {result.type}",
        )

    # ---------------------------------------------------------
    # REAL SETTLEMENT
    # ---------------------------------------------------------
    logger.info("========== X402 SETTLEMENT REQUEST ==========")
    logger.info("payment_payload=%r", result.payment_payload)
    logger.info("payment_requirements=%r", result.payment_requirements)
    logger.info("=============================================")
    settle_result = http_server.process_settlement(
        result.payment_payload,
        result.payment_requirements,
    )
    logger.error("========== X402 SETTLEMENT RESULT ==========")
    logger.error("type=%s", type(settle_result))
    logger.error("success=%s", getattr(settle_result, "success", None))
    logger.error("transaction=%s", getattr(settle_result, "transaction", None))
    logger.error("network=%s", getattr(settle_result, "network", None))
    logger.error("payer=%s", getattr(settle_result, "payer", None))
    logger.error("error_reason=%s", getattr(settle_result, "error_reason", None))
    logger.error("errorReason=%s", getattr(settle_result, "errorReason", None))
    logger.error("result=%r", settle_result)
    logger.error("============================================")
    logger.info("========== X402 SETTLEMENT RESULT ==========")
    logger.info("success=%s", settle_result.success)
    logger.info("transaction=%r", settle_result.transaction)
    logger.info("network=%r", settle_result.network)
    logger.info("payer=%r", settle_result.payer)
    logger.info("error_reason=%r", settle_result.error_reason)
    logger.info("headers=%r", settle_result.headers)
    logger.info("============================================")

    if not settle_result.success:
        logger.error(
            "X402 SETTLEMENT FAILED: success=%s transaction=%r "
            "network=%r payer=%r error=%r",
            settle_result.success,
            settle_result.transaction,
            settle_result.network,
            settle_result.payer,
            settle_result.error_reason,
        )

        return JSONResponse(
            status_code=402,
            content={
                "error": "Settlement failed",
                "details": str(settle_result.error_reason),
                "transaction": settle_result.transaction,
                "network": settle_result.network,
                "payer": settle_result.payer,
            },
        )

    # Genuine on-chain settlement succeeded.
    real_tx_id = settle_result.transaction
    real_network = settle_result.network
    payer = settle_result.payer or "unknown-payer"

    cfg = TIER_PRICING[tier]

    # Create the AgentLicense only after real payment settlement.
    license_obj = create_license(
        db=db,
        resource_id=resource_id,
        buyer=payer,
        seller=settings.avm_address,
        price=int(cfg["amount_micro_usdc"]) / 1_000_000,
        currency="USDC",
        usage_limit=cfg["usage_limit"],
        commercial_use=cfg["commercial_use"],
        redistribution_allowed=cfg["redistribution_allowed"],
        training_allowed=cfg["training_allowed"],
        duration_days=cfg["duration_days"],
        payment_reference=real_tx_id,
        algorand_tx_id=real_tx_id,
    )

    # ---------------------------------------------------------
    # PAYMENT AUDIT RECORD
    # ---------------------------------------------------------

    import uuid
    from datetime import datetime

    payment_row = Payment(
        id=f"pay_{uuid.uuid4().hex[:16]}",
        license_id=license_obj.id,
        amount=license_obj.price,
        currency="USDC",
        network=real_network or settings.algorand_network,
        transaction_id=real_tx_id,
        status=PaymentStatus.SETTLED,
        payment_method="x402-avm",
        verified_at=datetime.utcnow(),
    )

    db.add(payment_row)
    db.commit()

    logger.info(
        "REAL x402 settlement: tier=%s resource=%s payer=%s tx=%s network=%s",
        tier,
        resource_id,
        payer,
        real_tx_id,
        real_network,
    )

    return JSONResponse(
        status_code=200,
        content={
            "status": "license_issued",
            "license_id": license_obj.id,
            "tier": tier,
            "resource_id": resource_id,
            "buyer": payer,
            "uses_remaining": license_obj.uses_remaining,
            "license_hash": license_obj.license_hash,
            "algorand_tx_id": real_tx_id,
            "network": real_network,
            "is_real_settlement": True,
        },
        headers=settle_result.headers,
    )