"""License management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.database import get_db
from app.db.models import License, LicenseStatus
from app.models import (
    LicenseSchema, AgentRequirement, AgentDecision, LicenseVerification
)
from app.licensing.license_service import (
    create_license, get_license, validate_license, consume_license_usage,
    verify_license_hash, get_license_schema
)
from app.agents.decision_engine import (
    select_best_license, explain_license_selection
)
from app.api.resources import DEMO_LICENSE_OPTIONS
from app.models import LicenseOption

router = APIRouter(prefix="/licenses", tags=["licenses"])


@router.get("", response_model=List[LicenseSchema])
def list_licenses(
    buyer: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List licenses with optional filtering."""
    
    query = db.query(License)
    
    if buyer:
        query = query.filter(License.buyer == buyer)
    
    if resource_id:
        query = query.filter(License.resource_id == resource_id)
    
    if status:
        try:
            status_enum = LicenseStatus[status.upper()]
            query = query.filter(License.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    licenses = query.all()
    return [LicenseSchema.from_orm(lic) for lic in licenses]


@router.get("/{license_id}", response_model=LicenseSchema)
def get_license_details(
    license_id: str,
    db: Session = Depends(get_db),
):
    """Get license details."""
    
    license = get_license(db, license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    return LicenseSchema.from_orm(license)


@router.post("/{resource_id}/select", response_model=AgentDecision)
def agent_select_license(
    resource_id: str,
    requirement: AgentRequirement,
    db: Session = Depends(get_db),
):
    """
    Agent autonomously selects a license based on requirements.
    
    This endpoint demonstrates the agent decision engine.
    """
    
    # Get available license options for resource
    options = DEMO_LICENSE_OPTIONS.get(resource_id, [])
    
    if not options:
        raise HTTPException(
            status_code=404,
            detail=f"No license options found for resource {resource_id}"
        )
    
    # Convert to LicenseOption models
    license_options = []
    for opt in options:
        license_options.append(LicenseOption(
            license_id=opt["license_id"],
            name=opt["name"],
            description=opt["description"],
            price=opt["price"],
            usage_limit=opt["usage_limit"],
            duration_days=opt.get("duration_days"),
            commercial_use=opt["commercial_use"],
            redistribution_allowed=opt["redistribution_allowed"],
            training_allowed=opt["training_allowed"],
        ))
    
    # Agent decision engine selects best license
    decision, _ = select_best_license(license_options, requirement)
    
    if not decision:
        raise HTTPException(
            status_code=400,
            detail="No compatible licenses found for requirements"
        )
    
    return decision


@router.post("/{resource_id}/explain-selection")
def explain_selection(
    resource_id: str,
    requirement: AgentRequirement,
    db: Session = Depends(get_db),
):
    """Get detailed explanation of license selection process."""
    
    # Get available license options
    options = DEMO_LICENSE_OPTIONS.get(resource_id, [])
    
    if not options:
        raise HTTPException(
            status_code=404,
            detail=f"No license options found for resource {resource_id}"
        )
    
    # Convert to LicenseOption models
    license_options = []
    for opt in options:
        license_options.append(LicenseOption(
            license_id=opt["license_id"],
            name=opt["name"],
            description=opt["description"],
            price=opt["price"],
            usage_limit=opt["usage_limit"],
            duration_days=opt.get("duration_days"),
            commercial_use=opt["commercial_use"],
            redistribution_allowed=opt["redistribution_allowed"],
            training_allowed=opt["training_allowed"],
        ))
    
    # Get detailed explanation
    explanation = explain_license_selection(license_options, requirement)
    
    return explanation


@router.get("/{license_id}/verify", response_model=LicenseVerification)
def verify_license(
    license_id: str,
    commercial_use: bool = False,
    redistribution: bool = False,
    training: bool = False,
    db: Session = Depends(get_db),
):
    """Verify license validity and permissions."""
    
    license = get_license(db, license_id)
    
    if not license:
        return LicenseVerification(
            license_id=license_id,
            valid=False,
            active=False,
            not_expired=False,
            has_uses=False,
            permissions_met=False,
            message="License not found",
        )
    
    # Validate license
    is_valid, message = validate_license(
        db, license_id, commercial_use, redistribution, training
    )
    
    # Verify hash integrity
    hash_valid, _ = verify_license_hash(db, license_id)
    
    return LicenseVerification(
        license_id=license_id,
        valid=is_valid,
        active=license.status == LicenseStatus.ACTIVE,
        not_expired=not (license.expires_at and license.expires_at < __import__('datetime').datetime.utcnow()),
        has_uses=license.uses_remaining > 0,
        permissions_met=True,  # All required permissions already checked in validate_license
        message=message if is_valid else message,
    )


@router.post("/{license_id}/consume")
def consume_license(
    license_id: str,
    client_address: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Consume one usage from license."""
    
    success, message = consume_license_usage(db, license_id, client_address)
    
    if not success:
        raise HTTPException(status_code=403, detail=message)
    
    license = get_license(db, license_id)
    
    return {
        "success": True,
        "message": message,
        "uses_remaining": license.uses_remaining,
        "status": license.status.value,
    }


@router.post("/{resource_id}/create-test-fixture")
def create_test_fixture_license(
    resource_id: str,
    usage_limit: int = 3,
    db: Session = Depends(get_db),
):
    """
    Create a test-fixture license (clearly labeled as NOT from real blockchain settlement).
    
    This endpoint is ONLY for frontend/UI testing of the license enforcement pipeline.
    It bypasses x402 and creates a license with a simulated transaction id.
    Never use in production.
    """
    from app.licensing.license_service import create_license
    
    lic = create_license(
        db=db,
        resource_id=resource_id,
        buyer="TESTFIXTURE_PAYER_NOT_REAL",
        seller="TESTFIXTURE_SELLER_NOT_REAL",
        price=0.01,
        usage_limit=usage_limit,
        commercial_use=False,
        payment_reference="TESTFIXTURE_simulated_for_UI_testing_only",
        algorand_tx_id="TESTFIXTURE_simulated_for_UI_testing_only",
    )
    
    return {
        "license_id": lic.id,
        "status": "created_test_fixture",
        "uses_remaining": lic.uses_remaining,
        "note": "This is a TEST FIXTURE license created by the /create-test-fixture endpoint. It is NOT from a real x402 settlement and does NOT have a real Algorand transaction ID.",
    }