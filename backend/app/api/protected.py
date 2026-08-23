"""
Protected resource access.

IMPORTANT DISTINCTION FROM THE REAL X402 PAYMENT STEP
-------------------------------------------------------
The actual money movement (real x402 protocol, real Algorand settlement)
happens exclusively at POST /x402/purchase/{tier} (see app/api/purchase.py),
which is genuinely wrapped by the official x402-avm SDK.

This module does NOT implement any part of the x402 protocol. It only
enforces AgentLicense's own, purely database-backed usage rights on top of
a license that must already have been issued by a real, settled payment.
The 402 response returned below when no license is presented is an
AgentLicense-level "you need a license" signal - it deliberately does NOT
use the PAYMENT-REQUIRED header or body shape, so it can never be confused
with (or mistaken for) a genuine x402 challenge. It simply points the caller
at the real x402-protected purchase endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json

from app.db.database import get_db
from app.db.models import Resource
from app.licensing.license_service import (
    validate_license,
    consume_license_usage,
    get_license,
)

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/{resource_id}/access")
def access_protected_resource(
    resource_id: str,
    license_id: str | None = Header(None),
    x_license_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Access a resource using a previously issued AgentLicense license.

    Returns:
    - 402 if no license reference is presented (with a pointer to the real
      x402-protected purchase endpoint - NOT itself an x402 challenge)
    - 403 if the referenced license is invalid, expired, or exhausted
    - 200 with resource data + updated uses_remaining if valid
    """

    effective_license_id = license_id or x_license_id

    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found",
        )

    if not effective_license_id:
        return JSONResponse(
            status_code=402,
            content={
                "status": "license_required",
                "message": (
                    "No AgentLicense license presented. This is an "
                    "application-level gate, not an x402 payment challenge. "
                    "Purchase a license via the real x402-protected endpoint "
                    "below, then retry this request with the returned "
                    "license_id."
                ),
                "resource_id": resource_id,
                "purchase_endpoint": (
                    f"POST /x402/purchase/{{tier}}?resource_id={resource_id}"
                ),
                "tiers": [
                    "single",
                    "multi",
                    "commercial",
                ],
                "note": (
                    "See /x402/status for current facilitator configuration."
                ),
            },
        )

    license_obj = get_license(
        db,
        effective_license_id,
    )

    if not license_obj:
        raise HTTPException(
            status_code=403,
            detail="Invalid license",
        )

    is_valid, message = validate_license(
        db,
        effective_license_id,
    )

    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail=message,
        )

    if license_obj.resource_id != resource_id:
        raise HTTPException(
            status_code=403,
            detail="License is for a different resource",
        )

    success, usage_message = consume_license_usage(
        db=db,
        license_id=effective_license_id,
    )

    if not success:
        raise HTTPException(
            status_code=403,
            detail=usage_message,
        )

    resource_data = {}

    if resource.data:
        try:
            resource_data = json.loads(resource.data)
        except (json.JSONDecodeError, TypeError):
            resource_data = {
                "raw": resource.data
            }

    return {
        "status": "ok",
        "resource_id": resource_id,
        "resource_name": resource.name,
        "description": resource.description,
        "data": resource_data,
        "license_id": effective_license_id,
        "uses_remaining": license_obj.uses_remaining,
        "algorand_tx_id": license_obj.algorand_tx_id,
        "message": usage_message,
    }


@router.get("/{resource_id}/preview")
def preview_resource(
    resource_id: str,
    db: Session = Depends(get_db),
):
    """Preview resource metadata (free, no license required)."""

    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id)
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found",
        )

    return {
        "id": resource.id,
        "name": resource.name,
        "description": resource.description,
        "provider": resource.provider,
        "requires_license": True,
        "available_since": resource.created_at.isoformat(),
    }