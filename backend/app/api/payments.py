"""Payment and x402 protocol endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, Header, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import License, Payment, PaymentStatus, LicenseStatus
from app.models import PaymentRequest, PaymentResponse, X402PaymentHeader
from app.payments.x402 import get_x402_facilitator
from app.licensing.license_service import create_license, get_license
from app.config import settings

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/initiate", response_model=PaymentResponse)
def initiate_payment(
    request: PaymentRequest,
    db: Session = Depends(get_db),
):
    """
    Initiate payment for a license.
    
    Returns payment instructions for x402 flow.
    """
    
    facilitator = get_x402_facilitator()
    
    # Validate license exists
    license = get_license(db, request.license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Check if already paid
    existing_payment = db.query(Payment).filter(
        Payment.license_id == request.license_id,
        Payment.status == PaymentStatus.VERIFIED
    ).first()
    
    if existing_payment:
        return PaymentResponse(
            payment_id=existing_payment.id,
            license_id=request.license_id,
            status="verified",
            transaction_id=existing_payment.transaction_id,
            payment_required=False,
        )
    
    # Initiate new payment
    payment_info = facilitator.initiate_payment(
        db=db,
        license_id=request.license_id,
        amount=request.amount or license.price,
        currency=request.currency,
        payer_address=request.buyer,
    )
    
    return PaymentResponse(
        payment_id=payment_info["payment_id"],
        license_id=request.license_id,
        status="initiated",
        payment_required=True,
        payment_method="x402",
    )


@router.post("/verify")
def verify_payment(
    payment_id: str = Query(...),
    transaction_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Verify payment transaction.
    
    Called by client after submitting x402 payment.
    """
    
    facilitator = get_x402_facilitator()
    
    verified, message, license_id = facilitator.verify_payment(
        db=db,
        payment_id=payment_id,
        transaction_id=transaction_id,
    )
    
    if not verified:
        raise HTTPException(status_code=402, detail=message)
    
    # Settle payment on Algorand
    settlement = facilitator.settle_payment(db, payment_id)
    
    return {
        "status": "verified",
        "message": message,
        "payment_id": payment_id,
        "license_id": license_id,
        "transaction_id": transaction_id,
        "settlement": settlement,
    }


@router.get("/status/{payment_id}")
def get_payment_status(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """Get payment status."""
    
    facilitator = get_x402_facilitator()
    status = facilitator.get_payment_status(db, payment_id)
    
    return status


@router.post("/create-license")
def create_new_license(
    resource_id: str = Query(...),
    buyer: str = Query(...),
    license_type: str = Query("single"),  # single, multi, commercial
    db: Session = Depends(get_db),
):
    """
    Create a new license (called after payment verification).
    
    This creates the actual license record in the database.
    """
    
    # Define license options by type
    license_configs = {
        "single": {
            "price": 0.01,
            "usage_limit": 1,
            "commercial_use": False,
            "duration_days": None,
        },
        "multi": {
            "price": 0.05,
            "usage_limit": 10,
            "commercial_use": False,
            "duration_days": 30,
        },
        "commercial": {
            "price": 0.20,
            "usage_limit": 100,
            "commercial_use": True,
            "duration_days": 90,
        },
    }
    
    config = license_configs.get(license_type, license_configs["single"])
    
    # Create license
    license = create_license(
        db=db,
        resource_id=resource_id,
        buyer=buyer,
        seller="AgentLicense Demo",
        price=config["price"],
        currency="USDC",
        usage_limit=config["usage_limit"],
        commercial_use=config["commercial_use"],
        redistribution_allowed=False,
        training_allowed=config["commercial_use"],
        duration_days=config.get("duration_days"),
    )
    
    return {
        "license_id": license.id,
        "status": "created",
        "uses_remaining": license.uses_remaining,
        "expires_at": license.expires_at.isoformat() if license.expires_at else None,
        "license_hash": license.license_hash,
    }