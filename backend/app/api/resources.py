"""Resource management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import json

from app.db.database import get_db
from app.db.models import Resource, License, LicenseStatus
from app.models import ResourceSchema, LicenseOption
from app.config import settings

router = APIRouter(prefix="/resources", tags=["resources"])


# Demo resources
DEMO_RESOURCES = [
    {
        "id": "market-dataset-001",
        "name": "Market Research Dataset",
        "description": "Synthetic market analysis dataset with 10K records of market behavior, pricing, and consumer patterns.",
        "provider": "AgentLicense Demo",
        "data": json.dumps({
            "records": 10000,
            "fields": ["date", "product_id", "price", "volume", "sentiment"],
            "sample": {
                "date": "2024-01-15",
                "product_id": "PROD_001",
                "price": 99.99,
                "volume": 1500,
                "sentiment": "positive",
            },
        }),
    },
    {
        "id": "nlp-model-002",
        "name": "Fine-tuned NLP Model",
        "description": "Pre-trained language model fine-tuned for financial text analysis with 95% accuracy on benchmark.",
        "provider": "AgentLicense Demo",
        "data": json.dumps({
            "model_type": "transformer",
            "size_mb": 250,
            "accuracy": 0.95,
            "languages": ["en"],
        }),
    },
    {
        "id": "api-access-003",
        "name": "Real-time Market API",
        "description": "Access to real-time market data API with historical data spanning 5 years.",
        "provider": "AgentLicense Demo",
        "data": json.dumps({
            "endpoints": ["quotes", "trades", "history"],
            "rate_limit": 1000,
            "retention_days": 1825,
        }),
    },
]

# Demo license options for each resource
DEMO_LICENSE_OPTIONS = {
    "market-dataset-001": [
        {
            "license_id": "opt_market_single",
            "name": "Single Use",
            "description": "One-time access to dataset",
            "price": 0.01,
            "usage_limit": 1,
            "commercial_use": False,
            "redistribution_allowed": False,
            "training_allowed": False,
        },
        {
            "license_id": "opt_market_multi",
            "name": "10-Use License",
            "description": "Up to 10 accesses over 30 days",
            "price": 0.05,
            "usage_limit": 10,
            "duration_days": 30,
            "commercial_use": False,
            "redistribution_allowed": False,
            "training_allowed": True,
        },
        {
            "license_id": "opt_market_commercial",
            "name": "Commercial License",
            "description": "Full commercial use rights, 100 uses, 90 days",
            "price": 0.20,
            "usage_limit": 100,
            "duration_days": 90,
            "commercial_use": True,
            "redistribution_allowed": True,
            "training_allowed": True,
        },
    ],
    "nlp-model-002": [
        {
            "license_id": "opt_nlp_single",
            "name": "Single Deployment",
            "description": "Deploy to one production environment",
            "price": 0.02,
            "usage_limit": 1,
            "commercial_use": False,
            "redistribution_allowed": False,
            "training_allowed": False,
        },
        {
            "license_id": "opt_nlp_business",
            "name": "Business License",
            "description": "Commercial deployment with 50 queries per minute",
            "price": 0.10,
            "usage_limit": 500,
            "commercial_use": True,
            "redistribution_allowed": False,
            "training_allowed": False,
        },
        {
            "license_id": "opt_nlp_enterprise",
            "name": "Enterprise License",
            "description": "Unlimited deployment, commercial use, training allowed",
            "price": 0.50,
            "usage_limit": 10000,
            "duration_days": 365,
            "commercial_use": True,
            "redistribution_allowed": True,
            "training_allowed": True,
        },
    ],
    "api-access-003": [
        {
            "license_id": "opt_api_starter",
            "name": "Starter",
            "description": "1000 requests/month",
            "price": 0.03,
            "usage_limit": 1,
            "commercial_use": False,
            "redistribution_allowed": False,
            "training_allowed": False,
        },
        {
            "license_id": "opt_api_pro",
            "name": "Professional",
            "description": "10000 requests/month with historical data",
            "price": 0.08,
            "usage_limit": 10,
            "commercial_use": True,
            "redistribution_allowed": False,
            "training_allowed": True,
        },
        {
            "license_id": "opt_api_enterprise",
            "name": "Enterprise",
            "description": "Unlimited requests with full API access",
            "price": 0.25,
            "usage_limit": 1000,
            "duration_days": 365,
            "commercial_use": True,
            "redistribution_allowed": True,
            "training_allowed": True,
        },
    ],
}


def _ensure_demo_resources(db: Session):
    """Ensure demo resources exist in database."""
    for res_data in DEMO_RESOURCES:
        existing = db.query(Resource).filter(Resource.id == res_data["id"]).first()
        if not existing:
            resource = Resource(**res_data)
            db.add(resource)
    db.commit()


@router.get("", response_model=List[ResourceSchema])
def list_resources(db: Session = Depends(get_db)):
    """List available resources."""
    
    # Ensure demo resources exist
    _ensure_demo_resources(db)
    
    resources = db.query(Resource).all()
    return [ResourceSchema.from_orm(r) for r in resources]


@router.get("/{resource_id}", response_model=ResourceSchema)
def get_resource(
    resource_id: str,
    db: Session = Depends(get_db),
):
    """Get specific resource."""
    
    _ensure_demo_resources(db)
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return ResourceSchema.from_orm(resource)


@router.get("/{resource_id}/licenses", response_model=List[LicenseOption])
def get_license_options(
    resource_id: str,
    db: Session = Depends(get_db),
):
    """Get available license options for a resource."""
    
    _ensure_demo_resources(db)
    
    # Verify resource exists
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Return demo options
    options = DEMO_LICENSE_OPTIONS.get(resource_id, [])
    
    license_options = []
    for opt in options:
        license_options.append(LicenseOption(
            license_id=opt["license_id"],
            name=opt["name"],
            description=opt["description"],
            price=opt["price"],
            currency="USDC",
            usage_limit=opt["usage_limit"],
            duration_days=opt.get("duration_days"),
            commercial_use=opt["commercial_use"],
            redistribution_allowed=opt["redistribution_allowed"],
            training_allowed=opt["training_allowed"],
        ))
    
    return license_options