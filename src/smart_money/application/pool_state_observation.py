"""Decode known pool account layouts; never represent a current read as historical."""
import base64
import hashlib

from smart_money.application.verified_swap_legs import ALPHABET, AMM, CPMM


def _pubkey(data: bytes) -> str:
    value = int.from_bytes(data, "big")
    result = ""
    while value:
        value, digit = divmod(value, 58)
        result = ALPHABET[digit] + result
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + result


def observe_pool_state(snapshot: dict, leg: dict, transaction_slot: int) -> dict:
    if type(transaction_slot) is not int or transaction_slot < 0:
        raise ValueError("invalid transaction slot")
    addresses = snapshot["addresses"]
    response = snapshot["response"]
    if response.get("error") or snapshot.get("commitment") != "finalized":
        raise ValueError("finalized successful account read required")
    result = response["result"]
    slot = result["context"]["slot"]
    if type(slot) is not int or slot < 0 or len(addresses) != len(set(addresses)) or len(addresses) != len(result["value"]):
        raise ValueError("invalid account context")
    account = result["value"][addresses.index(leg["pool"])]
    if not isinstance(account, dict) or account.get("executable") is not False or account.get("owner") != leg["program"]:
        raise ValueError("pool owner mismatch or missing account")
    if account["data"][1] != "base64":
        raise ValueError("base64 account required")
    data = base64.b64decode(account["data"][0], validate=True)
    if leg["program"] == CPMM:
        if len(data) != 637 or data[:8] != hashlib.sha256(b"account:PoolState").digest()[:8]:
            raise ValueError("unsupported CPMM state")
        vaults = [_pubkey(data[i:i+32]) for i in (72, 104)]
        mints = [_pubkey(data[i:i+32]) for i in (168, 200)]
        status = data[329]
    elif leg["program"] == AMM:
        if len(data) != 752:
            raise ValueError("unsupported AMM state")
        vaults = [_pubkey(data[i:i+32]) for i in (336, 368)]
        mints = [_pubkey(data[i:i+32]) for i in (400, 432)]
        status = int.from_bytes(data[:8], "little")
    else:
        raise ValueError("unsupported pool program")
    if set(mints) != {leg["input_mint"], leg["output_mint"]}:
        raise ValueError("pool mint mismatch")
    by_mint = dict(zip(mints, vaults))
    if by_mint[leg["input_mint"]] != leg["input_vault"] or by_mint[leg["output_mint"]] != leg["output_vault"]:
        raise ValueError("pool vault mismatch")
    return {"pool": leg["pool"], "owner": account["owner"], "observed_slot": slot,
            "transaction_slot": transaction_slot, "historical_state_verified": False,
            "temporal_relation": "AFTER" if slot > transaction_slot else "SAME_SLOT" if slot == transaction_slot else "BEFORE",
            "mints": mints, "vaults": vaults, "status_raw": status,
            "account_sha256": hashlib.sha256(data).hexdigest(), "identity_matches": True}
