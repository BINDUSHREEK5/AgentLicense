"""License service for managing licenses and rights."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.models import (
    License, LicenseStatus, Resource, LicenseUsage, Payment, PaymentStatus
)
from app.models import LicenseSchema


def generate_license_hash(license_data: dict) -> str:
    """Generate deterministic hash for license."""
    # Create canonical JSON representation
    canonical = json.dumps(
        {
            "resource_id": license_data.get("resource_id"),
            "buyer": license_data.get("buyer"),
            "seller": license_data.get("seller"),
            "price": license_data.get("price"),
            "currency": license_data.get("currency"),
            "usage_limit": license_data.get("usage_limit"),
            "commercial_use": license_data.get("commercial_use"),
            "redistribution_allowed": license_data.get("redistribution_allowed"),
            "training_allowed": license_data.get("training_allowed"),
            "expires_at": str(license_data.get("expires_at")),
        },
        sort_keys=True,
        separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_license(
    db: Session,
    resource_id: str,
    buyer: str,
    seller: str = "AgentLicense Demo",
    price: float = 0.01,
    currency: str = "USDC",
    usage_limit: int = 1,
    commercial_use: bool = False,
    redistribution_allowed: bool = False,
    training_allowed: bool = False,
    duration_days: Optional[int] = None,
    payment_reference: Optional[str] = None,
    algorand_tx_id: Optional[str] = None,
) -> License:
    """Create a new license."""
    
    license_id = f"lic_{uuid.uuid4().hex[:16]}"
    
    expires_at = None
    if duration_days:
        expires_at = datetime.utcnow() + timedelta(days=duration_days)
    
    license_data = {
        "resource_id": resource_id,
        "buyer": buyer,
        "seller": seller,
        "price": price,
        "currency": currency,
        "usage_limit": usage_limit,
        "commercial_use": commercial_use,
        "redistribution_allowed": redistribution_allowed,
        "training_allowed": training_allowed,
        "expires_at": expires_at,
    }
    
    license_hash = generate_license_hash(license_data)
    
    license = License(
        id=license_id,
        resource_id=resource_id,
        buyer=buyer,
        seller=seller,
        price=price,
        currency=currency,
        usage_limit=usage_limit,
        uses_remaining=usage_limit,
        commercial_use=commercial_use,
        redistribution_allowed=redistribution_allowed,
        training_allowed=training_allowed,
        expires_at=expires_at,
        status=LicenseStatus.ACTIVE,
        payment_reference=payment_reference,
        algorand_tx_id=algorand_tx_id,
        license_hash=license_hash,
    )
    
    db.add(license)
    db.commit()
    db.refresh(license)
    return license


def get_license(db: Session, license_id: str) -> Optional[License]:
    """Get license by ID."""
    return db.query(License).filter(License.id == license_id).first()


def get_user_licenses(db: Session, buyer: str) -> List[License]:
    """Get all licenses for a buyer."""
    return db.query(License).filter(License.buyer == buyer).all()


def validate_license(
    db: Session,
    license_id: str,
    commercial_use: bool = False,
    redistribution: bool = False,
    training: bool = False,
) -> tuple[bool, str]:
    """Validate license for access."""
    
    license = get_license(db, license_id)
    
    if not license:
        return False, "License not found"
    
    if license.status != LicenseStatus.ACTIVE:
        return False, f"License is {license.status.value}"
    
    if license.expires_at and datetime.utcnow() > license.expires_at:
        return False, "License has expired"
    
    if license.uses_remaining <= 0:
        return False, "License usage exhausted"
    
    if commercial_use and not license.commercial_use:
        return False, "Commercial use not permitted"
    
    if redistribution and not license.redistribution_allowed:
        return False, "Redistribution not permitted"
    
    if training and not license.training_allowed:
        return False, "Training use not permitted"
    
    return True, "License is valid"


def consume_license_usage(
    db: Session,
    license_id: str,
    client_address: Optional[str] = None,
) -> tuple[bool, str]:
    """Consume one usage from license."""
    
    license = get_license(db, license_id)
    
    if not license:
        return False, "License not found"
    
    if license.uses_remaining <= 0:
        return False, "No uses remaining"
    
    # Decrement usage
    license.uses_remaining -= 1
    
    # Update status if exhausted
    if license.uses_remaining == 0:
        license.status = LicenseStatus.EXHAUSTED
    
    # Record usage
    usage = LicenseUsage(
        id=f"usage_{uuid.uuid4().hex[:16]}",
        license_id=license_id,
        access_method="api",
        client_address=client_address,
        success=True,
    )
    
    db.add(usage)
    db.commit()
    db.refresh(license)
    
    return True, f"Usage consumed. {license.uses_remaining} uses remaining"


def verify_license_hash(db: Session, license_id: str) -> tuple[bool, str]:
    """Verify license hash integrity."""
    
    license = get_license(db, license_id)
    
    if not license:
        return False, "License not found"
    
    license_data = {
        "resource_id": license.resource_id,
        "buyer": license.buyer,
        "seller": license.seller,
        "price": license.price,
        "currency": license.currency,
        "usage_limit": license.usage_limit,
        "commercial_use": license.commercial_use,
        "redistribution_allowed": license.redistribution_allowed,
        "training_allowed": license.training_allowed,
        "expires_at": license.expires_at,
    }
    
    computed_hash = generate_license_hash(license_data)
    
    if computed_hash == license.license_hash:
        return True, "License hash verified"
    
    return False, "License hash mismatch - possible tampering"


def get_license_schema(db: Session, license_id: str) -> Optional[LicenseSchema]:
    """Get license as schema."""
    license = get_license(db, license_id)
    if license:
        return LicenseSchema.from_orm(license)
    return None