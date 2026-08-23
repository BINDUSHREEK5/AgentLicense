import os
import asyncio
import base64

import algosdk
from algosdk import account, encoding

from dotenv import load_dotenv

from x402 import x402Client
from x402.mechanisms.avm.exact import ExactAvmScheme


class BuyerSigner:
    """x402 Algorand signer backed by an Algorand private key."""

    def __init__(self, private_key: str):
        self.private_key = private_key
        self._address = account.address_from_private_key(private_key)

    @property
    def address(self) -> str:
        return self._address

    def sign_transactions(
        self,
        unsigned_txns: list[bytes],
        indexes_to_sign: list[int],
    ) -> list[bytes | None]:
        result = []

        for i, txn_bytes in enumerate(unsigned_txns):
            if i in indexes_to_sign:
                txn = encoding.msgpack_decode(txn_bytes)
                signed = txn.sign(self.private_key)
                result.append(encoding.msgpack_encode(signed))
            else:
                result.append(None)

        return result


async def main():
    load_dotenv(".env", override=True)

    private_key = os.getenv("BUYER_PRIVATE_KEY")

    if not private_key:
        raise RuntimeError("BUYER_PRIVATE_KEY is missing from .env")

    signer = BuyerSigner(private_key)

    expected = "CGFQMVJMHKUMDGQNSTF2JMUQZKKHZ76F75Y4CSZFUURUBQDNVQCFJFCMZ4"

    print("Buyer address:", signer.address)

    if signer.address != expected:
        raise RuntimeError(
            f"Buyer address mismatch!\n"
            f"Expected: {expected}\n"
            f"Derived:  {signer.address}"
        )

    print("Buyer address MATCH: True")

    client = x402Client()

    ExactAvmScheme(
        signer=signer,
        algod_url="https://testnet-api.algonode.cloud",
    )

    client.register(
        "algorand:*",
        ExactAvmScheme(
            signer=signer,
            algod_url="https://testnet-api.algonode.cloud",
        ),
    )

    import httpx

    url = (
        "http://localhost:8000/"
        "x402/purchase/single"
        "?resource_id=nlp-model-002"
    )

    async with httpx.AsyncClient() as http:
        print("\n1. Requesting protected resource...")

        response = await http.post(url)

        print("HTTP status:", response.status_code)

        if response.status_code != 402:
            print("Response:", response.text)
            raise RuntimeError(
                f"Expected HTTP 402, got {response.status_code}"
            )

        payment_required_header = response.headers.get("payment-required")

        if not payment_required_header:
            raise RuntimeError("Missing payment-required header")

        print("Received HTTP 402 Payment Required")

        payment_required_bytes = base64.b64decode(payment_required_header)

        print("Payment requirements received")

        # x402Client expects the decoded PaymentRequired object.
        from x402.schemas.v2 import PaymentRequired

        payment_required = PaymentRequired.model_validate_json(
            payment_required_bytes
        )

        print(
            "Accepted requirements:",
            len(payment_required.accepts),
        )

        for requirement in payment_required.accepts:
            print(
                " -",
                requirement.scheme,
                requirement.network,
                "amount=",
                requirement.amount,
            )

        print("\n2. Creating Algorand x402 payment...")

        payment_payload = await client.create_payment_payload(
            payment_required
        )

        print("Payment payload created successfully")

        print("\n3. Sending signed payment to server...")

        # x402 V2 payment is normally sent in PAYMENT-SIGNATURE.
        import json

        payment_json = payment_payload.model_dump(
            by_alias=True,
            exclude_none=True,
        )

        payment_header = base64.b64encode(
            json.dumps(payment_json).encode()
        ).decode()

        paid_response = await http.post(
            url,
            headers={
                "PAYMENT-SIGNATURE": payment_header,
            },
        )

        print("\nFinal HTTP status:", paid_response.status_code)
        print("Final response:", paid_response.text)

        if paid_response.status_code == 200:
            print("\nSUCCESS: x402 purchase completed!")

        elif paid_response.status_code == 402:
            print("\nPayment was rejected or another payment is required.")

        else:
            print("\nPurchase failed.")


if __name__ == "__main__":
    asyncio.run(main())