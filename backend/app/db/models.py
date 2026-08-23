"""Database models for AgentLicense."""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class Resource(Base):
    """Digital resource available for licensing."""
    
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    data = Column(Text, nullable=True)  # JSON-serialized resource data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    licenses = relationship("License", back_populates="resource")


class LicenseStatus(str, enum.Enum):
    """License status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"
    REVOKED = "revoked"


class License(Base):
    """Machine-readable license for resource usage."""
    
    __tablename__ = "licenses"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    buyer = Column(String, nullable=False, index=True)
    seller = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USDC")
    usage_limit = Column(Integer, nullable=False)
    uses_remaining = Column(Integer, nullable=False)
    commercial_use = Column(Boolean, default=False)
    redistribution_allowed = Column(Boolean, default=False)
    training_allowed = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    status = Column(Enum(LicenseStatus), default=LicenseStatus.ACTIVE, index=True)
    payment_reference = Column(String, nullable=True, index=True)
    algorand_tx_id = Column(String, nullable=True, index=True)
    license_hash = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resource = relationship("Resource", back_populates="licenses")
    payments = relationship("Payment", back_populates="license")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_license_buyer_status", "buyer", "status"),
        Index("ix_license_resource_active", "resource_id", "status"),
    )


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    SETTLED = "settled"


class Payment(Base):
    """Payment transaction record."""
    
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, index=True)
    license_id = Column(String, ForeignKey("licenses.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USDC")
    network = Column(String, nullable=False)  # algorand, ethereum, etc.
    transaction_id = Column(String, nullable=True, index=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    payment_method = Column(String, default="x402")  # x402, direct, etc.
    payment_metadata = Column(Text, nullable=True)  # JSON-serialized metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    license = relationship("License", back_populates="payments")
    
    __table_args__ = (
        Index("ix_payment_license_status", "license_id", "status"),
    )


class LicenseUsage(Base):
    """Audit trail for license usage."""
    
    __tablename__ = "license_usage"
    
    id = Column(String, primary_key=True, index=True)
    license_id = Column(String, ForeignKey("licenses.id"), nullable=False, index=True)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    access_method = Column(String, nullable=False)  # api, direct, etc.
    client_address = Column(String, nullable=True)
    success = Column(Boolean, default=True)
    usage_metadata = Column(Text, nullable=True)  # JSON-serialized metadata