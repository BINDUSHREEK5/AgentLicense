"""Verify a local Algorand buyer mnemonic without network or secret output."""

import os
import sys

from algosdk import account, mnemonic


EXPECTED_ADDRESS = os.environ.get("BUYER_ADDRESS", "").strip()
MNEMONIC_VALUE = os.environ.get("BUYER_MNEMONIC", "").strip()


def main() -> int:
    if not MNEMONIC_VALUE:
        print("BUYER_MNEMONIC is not set.", file=sys.stderr)
        return 2

    if not EXPECTED_ADDRESS:
        print("BUYER_ADDRESS is not set.", file=sys.stderr)
        return 2

    try:
        private_key = mnemonic.to_private_key(MNEMONIC_VALUE)
        derived_address = account.address_from_private_key(private_key)
    except Exception as exc:
        print(f"Invalid Algorand mnemonic: {exc}", file=sys.stderr)
        return 2

    if derived_address != EXPECTED_ADDRESS:
        print("Derived address does not match BUYER_ADDRESS.", file=sys.stderr)
        return 1

    # Keep the derived AVM private-key representation in memory only.
    _avm_private_key = private_key
    del _avm_private_key

    print(derived_address)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())