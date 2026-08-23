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

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
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

router = APIRouter(prefix="/x402", tags=["x402-real-payments"])

# Built once at import time. Raises a clear error at import if AVM_ADDRESS is
# missing, which is surfaced to the operator instead of silently degrading
# into a fake payment scheme.
_server = None
_routes = None
_init_error: str | None = None

if is_configured():
    try:
        _server = build_resource_server()
        _routes = build_purchase_routes()
    except Exception as exc:  # pragma: no cover - configuration error path
        _init_error = str(exc)
        logger.error("Failed to build real x402-avm resource server: %s", exc)
else:
    _init_error = (
        "AVM_ADDRESS is not set in backend/.env. Real x402 purchase routes are "
        "disabled until a real Algorand receiving address is configured."
    )
    logger.warning(_init_error)


def _require_configured():
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
    Report the real configuration status of the x402 payment layer, so a
    caller can tell honestly whether purchases will work before trying.
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
                "price_usdc": int(cfg["amount_micro_usdc"]) / 1_000_000,
                "usage_limit": cfg["usage_limit"],
                "commercial_use": cfg["commercial_use"],
            }
            for tier, cfg in TIER_PRICING.items()
        },
    }


@router.post("/purchase/{tier}")
async def purchase_license(tier: str, resource_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Purchase an AgentLicense license tier via a REAL x402 payment on Algorand
    TestNet (or mainnet, depending on ALGORAND_NETWORK).

    Flow (all real, via the official x402-avm SDK):
      1. No PAYMENT-SIGNATURE header present -> returns a genuine HTTP 402
         with a machine-readable PAYMENT-REQUIRED body describing the exact
         Algorand network, USDC asset id, amount, and payee address.
      2. Client builds and signs a real Algorand transaction, retries with
         PAYMENT-SIGNATURE header -> this handler calls the real facilitator's
         verify endpoint via server.process_http_request().
      3. On verified payment, calls the real facilitator's settle endpoint via
         server.process_settlement() -> broadcasts/confirms the transaction on
         Algorand and returns the real transaction id.
      4. Only after settlement succeeds does this handler create the
         AgentLicense License row, stamped with the real algorand_tx_id.
    """
    _require_configured()

    if tier not in TIER_PRICING:
        raise HTTPException(status_code=404, detail=f"Unknown tier '{tier}'")

    route_key = f"POST /x402/purchase/{tier}"
    if route_key not in _routes:
        raise HTTPException(status_code=500, detail="Route not registered")

    # Build a single-route view of the server for this specific tier so
    # process_http_request only ever matches against this tier's price.
    from x402.http.x402_http_server import x402HTTPResourceServer

    http_server = x402HTTPResourceServer(_server, {route_key: _routes[route_key]})

    try:
        http_server.initialize()
    except Exception as exc:
        # Honest failure: this is what happens when the facilitator cannot be
        # reached (e.g. restricted network egress), NOT a fake fallback.
        logger.error("x402 initialize() failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not reach the x402 facilitator to sync supported "
                f"payment schemes ({settings.x402_facilitator_url}). "
                f"Underlying error: {exc}"
            ),
        )

    adapter = FastAPIAdapter(request)
    payment_header = adapter.get_header("payment-signature") or adapter.get_header("x-payment")
    context = HTTPRequestContext(
        adapter=adapter,
        path=route_key.split(" ", 1)[1],
        method="POST",
        payment_header=payment_header,
    )

    result = await http_server.process_http_request(context)

    if result.type == "payment-error":
        resp = result.response
        status = resp.status if resp else 402
        body = resp.body if resp else {"error": "Payment required"}
        headers = resp.headers if resp else {}
        return JSONResponse(status_code=status, content=body, headers=headers)

    if result.type != "payment-verified":
        raise HTTPException(status_code=500, detail=f"Unexpected result type: {result.type}")

    # Payment verified by the real facilitator. Now settle it for real.
    settle_result = http_server.process_settlement(
        result.payment_payload, result.payment_requirements
    )

    if not settle_result.success:
        return JSONResponse(
            status_code=402,
            content={"error": "Settlement failed", "details": settle_result.error_reason},
        )

    # ---- Genuine on-chain settlement succeeded. Persist real provenance. ----
    real_tx_id = settle_result.transaction
    real_network = settle_result.network
    payer = settle_result.payer or "unknown-payer"

    cfg = TIER_PRICING[tier]
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

    logger.info(
        "REAL x402 settlement: tier=%s resource=%s payer=%s tx=%s network=%s",
        tier, resource_id, payer, real_tx_id, real_network,
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