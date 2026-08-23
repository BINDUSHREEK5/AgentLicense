"""Pydantic models for API schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class LicenseOption(BaseModel):
    """License option available for a resource."""
    
    license_id: str
    name: str
    description: str
    price: float
    currency: str = "USDC"
    usage_limit: int
    duration_days: Optional[int] = None
    expires_at: Optional[datetime] = None
    commercial_use: bool
    redistribution_allowed: bool
    training_allowed: bool


class AgentRequirement(BaseModel):
    """Requirements for license selection by agent."""
    
    task: str
    budget: float
    required_uses: int = 1
    commercial_use_required: bool = False
    redistribution_required: bool = False
    training_required: bool = False
    duration_days: Optional[int] = None


class AgentDecision(BaseModel):
    """Agent decision for license selection."""
    
    selected_license_id: str
    reason: str
    confidence: float = 1.0


class ResourceSchema(BaseModel):
    """Resource representation."""
    
    id: str
    name: str
    description: str
    provider: str
    
    model_config = {"from_attributes": True}


class LicenseSchema(BaseModel):
    """License representation."""
    
    id: str
    resource_id: str
    buyer: str
    seller: str
    price: float
    currency: str = "USDC"
    usage_limit: int
    uses_remaining: int
    commercial_use: bool
    redistribution_allowed: bool
    training_allowed: bool
    expires_at: Optional[datetime] = None
    status: str
    payment_reference: Optional[str] = None
    algorand_tx_id: Optional[str] = None
    license_hash: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PaymentRequest(BaseModel):
    """Payment request for license."""
    
    license_id: str
    buyer: str
    amount: float
    currency: str = "USDC"


class PaymentResponse(BaseModel):
    """Payment response."""
    
    payment_id: str
    license_id: str
    status: str
    transaction_id: Optional[str] = None
    payment_required: bool = False
    payment_method: str = "x402"


class LicenseVerification(BaseModel):
    """License verification result."""
    
    license_id: str
    valid: bool
    active: bool
    not_expired: bool
    has_uses: bool
    permissions_met: bool
    message: str


class X402PaymentHeader(BaseModel):
    """x402 Payment Required header information."""
    
    payment_required: bool = True
    payment_method: str = "x402"
    license_id: str
    amount: float
    currency: str = "USDC"
    facilitator_url: str
    asset_id: str


class DemoTransactionInfo(BaseModel):
    """Demo mode transaction information."""
    
    mode: str = "demo"
    transaction_id: str
    is_real: bool = False
    note: str


class HealthCheck(BaseModel):
    """Health check response."""
    
    status: str
    version: str = "1.0.0"
    environment: str
    database: bool
    algorand: Optional[bool] = None
    demo_mode: bool