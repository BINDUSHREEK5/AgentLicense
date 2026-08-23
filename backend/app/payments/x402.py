"""x402 payment integration for AgentLicense."""

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Payment, PaymentStatus, License
from app.blockchain.algorand import get_algorand_client

logger = logging.getLogger(__name__)


class X402PaymentFacilitator:
    """
    AgentLicense x402 integration.

    This class manages our database payment records.

    The actual HTTP x402 verification/settlement is handled by the
    x402 AVM middleware that will be registered in app.main.
    """

    def __init__(self):
        self.facilitator_url = settings.x402_facilitator_url
        self.network = settings.algorand_network
        self.asset_id = settings.algorand_asset_id
        self.algorand = get_algorand_client()

    def create_payment_requirement(
        self,
        license_id: str,
        amount: float,
        currency: str = "USDC",
    ) -> Dict[str, Any]:
        """
        Return basic information used to construct an x402 requirement.

        The actual PAYMENT-REQUIRED response is produced by the x402
        middleware, not by manually-created headers.
        """

        return {
            "license_id": license_id,
            "amount": amount,
            "currency": currency,
            "network": self.network,
            "asset_id": self.asset_id,
            "pay_to": settings.avm_address,
            "facilitator_url": self.facilitator_url,
        }

    def initiate_payment(
        self,
        db: Session,
        license_id: str,
        amount: float,
        currency: str = "USDC",
        payer_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create our internal payment record.

        This does NOT claim that money has been paid.
        """

        license = (
            db.query(License)
            .filter(License.id == license_id)
            .first()
        )

        if not license:
            raise ValueError("License not found")

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")

        payment_id = f"pay_{uuid.uuid4().hex[:16]}"

        payment = Payment(
            id=payment_id,
            license_id=license_id,
            amount=amount,
            currency=currency,
            network=self.network,
            status=PaymentStatus.PENDING,
            payment_method="x402",
            payment_metadata=(
                f'{{"payer_address": "{payer_address}"}}'
                if payer_address
                else None
            ),
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "payment_id": payment.id,
            "license_id": license_id,
            "amount": amount,
            "currency": currency,
            "network": self.network,
            "asset_id": self.asset_id,
            "status": "pending",
            "payment_method": "x402",
            "facilitator_url": self.facilitator_url,
            "pay_to": settings.avm_address,
        }

    def mark_payment_settled(
        self,
        db: Session,
        payment_id: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Mark a payment as settled after REAL x402 settlement.

        This function should only be called after the x402 server/
        facilitator reports successful settlement.
        """

        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id)
            .first()
        )

        if not payment:
            return {
                "status": "error",
                "message": "Payment not found",
            }

        if not transaction_id:
            return {
                "status": "error",
                "message": "Transaction ID is required",
            }

        payment.transaction_id = transaction_id
        payment.status = PaymentStatus.SETTLED

        license = (
            db.query(License)
            .filter(License.id == payment.license_id)
            .first()
        )

        if not license:
            db.rollback()
            return {
                "status": "error",
                "message": "License not found",
            }

        license.payment_reference = payment.id
        license.algorand_tx_id = transaction_id

        db.commit()

        return {
            "status": "settled",
            "payment_id": payment.id,
            "license_id": license.id,
            "transaction_id": transaction_id,
            "is_real": not settings.demo_mode,
        }

    def get_payment_status(
        self,
        db: Session,
        payment_id: str,
    ) -> Dict[str, Any]:
        """Get current payment status."""

        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id)
            .first()
        )

        if not payment:
            return {
                "status": "not_found",
                "payment_id": payment_id,
            }

        return {
            "payment_id": payment.id,
            "license_id": payment.license_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "network": payment.network,
            "status": payment.status.value,
            "transaction_id": payment.transaction_id,
            "created_at": (
                payment.created_at.isoformat()
                if payment.created_at
                else None
            ),
            "verified_at": (
                payment.verified_at.isoformat()
                if payment.verified_at
                else None
            ),
        }


# Global instance
x402_facilitator = X402PaymentFacilitator()


def get_x402_facilitator() -> X402PaymentFacilitator:
    """Get the global x402 service."""
    return x402_facilitator