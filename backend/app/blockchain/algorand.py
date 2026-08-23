"""Algorand blockchain integration for AgentLicense."""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class AlgorandClient:
    """Client for Algorand blockchain interactions."""

    def __init__(self):
        self.network = settings.algorand_network
        self.algod_url = settings.algorand_algod_url
        self.indexer_url = settings.algorand_indexer_url
        self.wallet_address = settings.avm_address
        self.private_key = settings.avm_private_key
        self.asset_id = settings.algorand_asset_id

        # Configuration exists, but demo mode still prevents real
        # blockchain operations.
        self.enabled = bool(
            self.wallet_address
            and self.algod_url
            and self.indexer_url
        )

        if self.enabled:
            logger.info(
                "Algorand configured: network=%s, algod=%s",
                self.network,
                self.algod_url,
            )
        else:
            logger.warning(
                "Algorand receiving address is not configured. "
                "Real blockchain operations are disabled."
            )

    def is_enabled(self) -> bool:
        """Return True when real Algorand operations may be used."""
        return self.enabled and not settings.demo_mode

    def is_configured(self) -> bool:
        """Return True when Algorand configuration is present."""
        return self.enabled

    def record_payment_provenance(
        self,
        license_id: str,
        payment_amount: float,
        payment_currency: str = "USDC",
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record payment provenance.

        Demo mode creates a clearly-marked simulated record.
        Real settlement will be handled by the x402 AVM integration.
        """

        if settings.demo_mode:
            return self._simulate_algorand_record(
                license_id=license_id,
                payment_amount=payment_amount,
                payment_currency=payment_currency,
                transaction_id=transaction_id,
            )

        if not self.is_enabled():
            return {
                "status": "skipped",
                "is_real": False,
                "reason": "Algorand is not configured",
            }

        # IMPORTANT:
        # Real x402 settlement will provide the transaction ID.
        #
        # This method should NOT invent a blockchain transaction.
        if not transaction_id:
            return {
                "status": "error",
                "is_real": False,
                "reason": "No settled Algorand transaction ID was provided",
            }

        return {
            "status": "confirmed",
            "is_real": True,
            "network": self.network,
            "transaction_id": transaction_id,
            "license_id": license_id,
            "amount": payment_amount,
            "currency": payment_currency,
            "asset_id": self.asset_id,
        }

    def _simulate_algorand_record(
        self,
        license_id: str,
        payment_amount: float,
        payment_currency: str = "USDC",
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a clearly-marked simulated transaction for demo mode."""

        if not transaction_id:
            demo_data = (
                f"{license_id}:"
                f"{payment_amount}:"
                f"{payment_currency}:"
                f"{datetime.utcnow().isoformat()}"
            )

            transaction_id = (
                "DEMO_"
                + hashlib.sha256(demo_data.encode()).hexdigest()[:32].upper()
            )

        return {
            "status": "simulated",
            "is_real": False,
            "network": self.network,
            "transaction_id": transaction_id,
            "license_id": license_id,
            "amount": payment_amount,
            "currency": payment_currency,
            "asset_id": self.asset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "DEMO",
            "note": (
                "Simulated transaction. "
                "No Algorand transaction was submitted."
            ),
        }

    def verify_transaction(
        self,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Verify an Algorand transaction.

        For now, demo transactions are recognized locally.
        Real transaction verification will be performed against
        Algorand/x402 settlement data.
        """

        if settings.demo_mode:
            return self._verify_demo_transaction(transaction_id)

        if not self.is_enabled():
            return {
                "status": "unavailable",
                "is_real": False,
                "transaction_id": transaction_id,
                "reason": "Algorand is not configured",
            }

        if not transaction_id:
            return {
                "status": "invalid",
                "is_real": False,
                "reason": "Transaction ID is required",
            }

        # Do NOT pretend an arbitrary transaction ID is confirmed.
        #
        # Real verification belongs to the x402 facilitator/AVM flow.
        return {
            "status": "requires_x402_verification",
            "is_real": True,
            "transaction_id": transaction_id,
            "network": self.network,
        }

    def _verify_demo_transaction(
        self,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """Verify a simulated transaction."""

        if transaction_id.startswith("DEMO_"):
            return {
                "status": "confirmed",
                "is_real": False,
                "transaction_id": transaction_id,
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "DEMO",
                "note": "This is a simulated transaction.",
            }

        return {
            "status": "not_found",
            "is_real": False,
            "transaction_id": transaction_id,
        }

    def get_account_balance(
        self,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return account balance information."""

        address = address or self.wallet_address

        if settings.demo_mode:
            return {
                "status": "simulated",
                "address": address,
                "balance": 1000.0,
                "currency": "USDC",
                "asset_id": self.asset_id,
                "is_real": False,
                "mode": "DEMO",
            }

        if not self.is_enabled():
            return {
                "status": "unavailable",
                "address": address,
                "is_real": False,
                "reason": "Algorand is not configured",
            }

        # Actual account lookup will be added when we wire the
        # Algorand SDK/x402 AVM settlement layer.
        return {
            "status": "configured",
            "address": address,
            "network": self.network,
            "asset_id": self.asset_id,
            "algod_url": self.algod_url,
            "indexer_url": self.indexer_url,
            "is_real": False,
            "note": "Account lookup not yet executed.",
        }


# Global instance
algorand = AlgorandClient()


def get_algorand_client() -> AlgorandClient:
    """Get the global Algorand client."""
    return algorand