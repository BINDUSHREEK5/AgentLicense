
#!/usr/bin/env python

from __future__ import annotations

import argparse
import base64
import os
import sys

import algosdk
import msgpack
import requests
from dotenv import load_dotenv

from x402.client import SchemeRegistration, x402ClientConfig
from x402.http.clients.requests import wrapRequestsWithPaymentFromConfig
from x402.mechanisms.avm import (
    ALGORAND_MAINNET_CAIP2,
    ALGORAND_TESTNET_CAIP2,
)
from x402.mechanisms.avm.exact import ExactAvmClientScheme


load_dotenv()


class AlgosdkSigner:
    """
    Real Algorand signer used by the official x402-avm client.

    x402-avm supplies raw msgpack transaction bytes.
    We decode those bytes, reconstruct the Algorand transaction,
    sign it using the configured private key, and return raw
    signed transaction bytes.
    """

    def __init__(self, private_key_b64: str):
        try:
            secret_key = base64.b64decode(
                private_key_b64,
                validate=True,
            )
        except Exception as exc:
            raise ValueError(
                "AVM_PRIVATE_KEY is not valid base64."
            ) from exc

        if len(secret_key) != 64:
            raise ValueError(
                "AVM_PRIVATE_KEY must decode to exactly 64 bytes. "
                f"Got {len(secret_key)} bytes."
            )

        self._private_key_b64 = private_key_b64
        self._secret_key = secret_key

        try:
            self._address = algosdk.account.address_from_private_key(
                private_key_b64
            )
        except Exception as exc:
            raise ValueError(
                f"Could not derive Algorand address from "
                f"AVM_PRIVATE_KEY: {exc}"
            ) from exc

    @property
    def address(self) -> str:
        return self._address

    def sign_transactions(
        self,
        unsigned_txns: list[bytes],
        indexes_to_sign: list[int],
    ):
        result = []

        for i, txn_data in enumerate(unsigned_txns):

            # This transaction belongs to another signer, e.g. fee payer.
            if i not in indexes_to_sign:
                result.append(None)
                continue

            try:
                if not isinstance(txn_data, bytes):
                    raise TypeError(
                        f"Expected raw bytes for transaction {i}, "
                        f"got {type(txn_data).__name__}"
                    )

                # x402-avm gives us RAW msgpack bytes here.
                txn_dict = msgpack.unpackb(
                    txn_data,
                    raw=False,
                )

                txn = algosdk.transaction.Transaction.undictify(
                    txn_dict
                )

                # py-algorand-sdk expects the private key string here.
                signed_txn = txn.sign(
                    self._private_key_b64
                )

                # SDK encoding returns base64 text.
                # Convert that back into raw bytes because x402 expects
                # the signer to return raw signed transaction bytes.
                signed_b64 = algosdk.encoding.msgpack_encode(
                    signed_txn
                )

                signed_bytes = base64.b64decode(
                    signed_b64
                )

                result.append(signed_bytes)

            except Exception as exc:
                print(
                    f"ERROR signing transaction {i}: {exc}",
                    file=sys.stderr,
                )
                raise

        return result

def main():
    parser = argparse.ArgumentParser(
        description="Real x402 Algorand payment demo client"
    )

    parser.add_argument(
        "--resource-id",
        default="market-dataset-001",
    )

    parser.add_argument(
        "--tier",
        default="single",
        choices=[
            "single",
            "multi",
            "commercial",
        ],
    )

    parser.add_argument(
        "--backend-url",
        default=os.environ.get(
            "AGENTLICENSE_BACKEND_URL",
            "http://localhost:8000",
        ),
    )

    parser.add_argument(
        "--network",
        default=os.environ.get(
            "ALGORAND_NETWORK",
            "testnet",
        ),
        choices=[
            "testnet",
            "mainnet",
        ],
    )

    args = parser.parse_args()

    # ---------------------------------------------------------
    # PRIVATE KEY
    # ---------------------------------------------------------

    private_key_b64 = os.environ.get(
        "AVM_PRIVATE_KEY",
        "",
    ).strip()

    if not private_key_b64:
        print(
            "ERROR: AVM_PRIVATE_KEY is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ---------------------------------------------------------
    # SIGNER
    # ---------------------------------------------------------

    try:
        signer = AlgosdkSigner(
            private_key_b64
        )
    except Exception as exc:
        print(
            f"ERROR: invalid AVM_PRIVATE_KEY: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"Payer address: {signer.address}"
    )

    # ---------------------------------------------------------
    # NETWORK
    # ---------------------------------------------------------

    if args.network == "testnet":
        network = ALGORAND_TESTNET_CAIP2
    else:
        network = ALGORAND_MAINNET_CAIP2

    print(
        f"Network: {args.network}"
    )

    # ---------------------------------------------------------
    # x402 CLIENT
    # ---------------------------------------------------------

    config = x402ClientConfig(
        schemes=[
            SchemeRegistration(
                network=network,
                client=ExactAvmClientScheme(
                    signer=signer,
                ),
            )
        ]
    )

    session = requests.Session()

    session = wrapRequestsWithPaymentFromConfig(
        session,
        config,
    )

    # ---------------------------------------------------------
    # PURCHASE URL
    # ---------------------------------------------------------

    backend_url = args.backend_url.rstrip("/")

    url = (
        f"{backend_url}"
        f"/x402/purchase/{args.tier}"
    )

    params = {
        "resource_id": args.resource_id,
    }

    print()
    print("=" * 70)
    print("AGENTLICENSE REAL x402 PAYMENT")
    print("=" * 70)
    print(
        f"POST:        {url}"
    )
    print(
        f"Resource:    {args.resource_id}"
    )
    print(
        f"Tier:        {args.tier}"
    )
    print("=" * 70)
    print()

    print(
        "Sending request..."
    )

    # ---------------------------------------------------------
    # REQUEST
    # ---------------------------------------------------------

    try:
        response = session.post(
            url,
            params=params,
            timeout=60,
        )

    except requests.exceptions.RequestException as exc:
        print()
        print(
            "ERROR: HTTP request failed."
        )
        print(
            f"Details: {exc}"
        )
        sys.exit(1)

    except Exception as exc:
        print()
        print(
            "ERROR: x402 payment creation/signing failed."
        )
        print(
            f"Details: {exc}"
        )
        sys.exit(1)

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    print()
    print(
        f"Final status code: {response.status_code}"
    )

    try:
        body = response.json()
    except ValueError:
        body = response.text

    print(
        "Response body:"
    )
    print(body)

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    if (
        response.status_code == 200
        and isinstance(body, dict)
        and body.get("is_real_settlement") is True
    ):
        print()
        print("=" * 70)
        print("REAL SETTLEMENT CONFIRMED")
        print("=" * 70)

        print(
            f"License ID:              {body.get('license_id')}"
        )

        print(
            f"Algorand transaction ID: {body.get('algorand_tx_id')}"
        )

        print(
            f"Network:                 {body.get('network')}"
        )

        print(
            f"Resource ID:             {body.get('resource_id')}"
        )

        print(
            f"Tier:                    {body.get('tier')}"
        )

        print(
            f"Buyer:                   {body.get('buyer')}"
        )

        print(
            f"Real settlement:         {body.get('is_real_settlement')}"
        )

        print("=" * 70)
        print()

        tx_id = body.get(
            "algorand_tx_id"
        )

        if tx_id:
            print(
                "Verify independently on Algorand TestNet:"
            )
            print(
                f"https://lora.algokit.io/testnet/transaction/{tx_id}"
            )

        sys.exit(0)

    # ---------------------------------------------------------
    # FAILURE
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("PAYMENT DID NOT SETTLE")
    print("=" * 70)

    if response.status_code == 402:
        print(
            "The server returned HTTP 402 Payment Required."
        )

    print(
        "Check the response above and the backend terminal logs."
    )

    print("=" * 70)

    sys.exit(1)


if __name__ == "__main__":
    main()
