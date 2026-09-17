"""Instruction-layout and transfer-verified legs; no guessed pool accounts.

Layouts: raydium-io/raydium-cp-swap instructions/swap_base_input.rs;
raydium-io/raydium-amm program/src/instruction.rs (SwapBaseInV2, tag 16).
Verification is relative to the supplied successful RPC fixture, not consensus.
"""
import hashlib

from smart_money.application.wallet_route_evidence import TOKEN_PROGRAMS

CPMM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"
AMM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
CLMM = "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
CLASSIC_TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _decode(value: str) -> bytes:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise ValueError("invalid instruction data")
    number = 0
    for char in value:
        if char not in ALPHABET:
            raise ValueError("invalid base58")
        number = number * 58 + ALPHABET.index(char)
    return b"\0" * (len(value) - len(value.lstrip("1"))) + number.to_bytes((number.bit_length() + 7) // 8, "big")


def _check_transfer_balances(raw: dict, route: dict) -> None:
    """Accept Token-2022 only when ALL raw account movements equal transfers.

    No fee/hook/extension support is implied: withheld fees, hooks, missing
    accounts and unknown token operations must fail this bounded verifier.
    """
    message, meta = raw["transaction"]["message"], raw["meta"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in message["accountKeys"]]
    pre = {keys[b["accountIndex"]]: b for b in meta["preTokenBalances"]}
    post = {keys[b["accountIndex"]]: b for b in meta["postTokenBalances"]}
    if pre.keys() != post.keys():
        raise ValueError("created/closed token accounts not supported here")
    amounts = dict.fromkeys(pre, 0)
    for edge in route["transfers"]:
        source, destination = edge["source"], edge["destination"]
        if source not in pre or destination not in pre:
            raise ValueError("missing transfer account")
        for address in (source, destination):
            if pre[address].get("programId") not in TOKEN_PROGRAMS or pre[address].get("programId") != post[address].get("programId"):
                raise ValueError("token account program unknown or changed")
        if pre[source]["programId"] != pre[destination]["programId"]:
            raise ValueError("token transfer program conflict")
        instructions = [message["instructions"][edge["outer"]]]
        instructions += next((g["instructions"] for g in meta["innerInstructions"] if g["index"] == edge["outer"]), [])
        if instructions[edge["position"]]["programId"] != pre[source]["programId"]:
            raise ValueError("transfer invoked wrong token program")
        amounts[source] -= int(edge["raw_amount"])
        amounts[destination] += int(edge["raw_amount"])
    for address in pre:
        delta = int(post[address]["uiTokenAmount"]["amount"]) - int(pre[address]["uiTokenAmount"]["amount"])
        if delta != amounts[address]:
            raise ValueError("transfer fee or unexplained account movement")


def verify_swap_legs(raw: dict, route: dict) -> dict:
    if raw["meta"]["err"] is not None:
        raise ValueError("failed transaction")
    legs, unresolved = [], []
    top = raw["transaction"]["message"]["instructions"]
    groups = {g["index"]: g["instructions"] for g in raw["meta"].get("innerInstructions", []) or []}
    for outer, instruction in enumerate(top):
        instructions = [instruction] + groups.get(outer, [])
        for position, ins in enumerate(instructions):
            program = ins.get("programId")
            if program not in {CPMM, AMM, CLMM}:
                continue
            try:
                data = _decode(ins.get("data"))
                accounts = ins["accounts"]
                height = 1 if position == 0 else ins.get("stackHeight")
                if type(height) is not int:
                    raise ValueError("missing stack height")
                if program == CPMM:
                    if len(data) != 24 or data[:8] != hashlib.sha256(b"global:swap_base_input").digest()[:8] or len(accounts) != 13:
                        raise ValueError("unsupported CPMM layout")
                    pool, source, destination, vault_in, vault_out = [accounts[i] for i in (3, 4, 5, 6, 7)]
                    if any(p not in TOKEN_PROGRAMS for p in accounts[8:10]):
                        raise ValueError("unsupported token program")
                    offset, name = 8, "swap_base_input"
                elif program == CLMM:
                    if len(data) != 41 or data[:8] != hashlib.sha256(b"global:swap_v2").digest()[:8] or data[40] != 1 or len(accounts) < 14:
                        raise ValueError("unsupported CLMM exact-input layout")
                    if accounts[8:11] != [CLASSIC_TOKEN, TOKEN_2022, "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"]:
                        raise ValueError("CLMM program accounts mismatch")
                    pool, source, destination, vault_in, vault_out = [accounts[i] for i in (2, 3, 4, 5, 6)]
                    offset, name = 8, "swap_v2_exact_input"
                else:
                    if len(data) != 17 or data[0] != 16 or len(accounts) != 8 or accounts[0] != CLASSIC_TOKEN:
                        raise ValueError("unsupported AMM layout")
                    pool, source, destination = accounts[1], accounts[5], accounts[6]
                    vault_in, vault_out = None, None
                    offset, name = 1, "SwapBaseInV2"
                if any(not isinstance(a, str) or not a for a in accounts):
                    raise ValueError("unresolved account")
                end = position + 1
                while end < len(instructions):
                    child_height = instructions[end].get("stackHeight")
                    if type(child_height) is not int:
                        raise ValueError("missing child stack height")
                    if child_height <= height:
                        break
                    end += 1
                transfers = [e for e in route["transfers"] if e["outer"] == outer and position < e["position"] < end]
                token_calls = [i for i in instructions[position + 1:end] if i.get("programId") in TOKEN_PROGRAMS]
                if len(transfers) != 2 or len(token_calls) != 2:
                    raise ValueError("expected two resolved transfers")
                if end - position != 3 or any(i.get("stackHeight") != height + 1 for i in token_calls):
                    raise ValueError("unsupported nested CPI or token hook")
                if any(i["programId"] == TOKEN_2022 for i in token_calls):
                    if route["gaps"] or any(i.get("parsed", {}).get("type") != "transferChecked" for i in token_calls):
                        raise ValueError("unsupported Token-2022 transfer")
                    _check_transfer_balances(raw, route)
                incoming = [e for e in transfers if e["source"] == source]
                outgoing = [e for e in transfers if e["destination"] == destination]
                if len(incoming) != 1 or len(outgoing) != 1 or incoming[0] is outgoing[0]:
                    raise ValueError("transfer endpoints mismatch")
                left, right = incoming[0], outgoing[0]
                if program in {CPMM, CLMM}:
                    mint_offset = 10 if program == CPMM else 11
                    if left["destination"] != vault_in or right["source"] != vault_out or [left["mint"], right["mint"]] != accounts[mint_offset:mint_offset+2]:
                        raise ValueError("pool vault or mint mismatch")
                    if program == CPMM and [i["programId"] for i in token_calls] != accounts[8:10]:
                        raise ValueError("CPMM token program binding mismatch")
                elif {left["destination"], right["source"]} != set(accounts[3:5]):
                    raise ValueError("AMM vault mismatch")
                amount, minimum = int.from_bytes(data[offset:offset+8], "little"), int.from_bytes(data[offset+8:offset+16], "little")
                if amount <= 0 or int(left["raw_amount"]) != amount or int(right["raw_amount"]) < minimum or int(right["raw_amount"]) <= 0 or left["mint"] == right["mint"]:
                    raise ValueError("swap amount mismatch")
                legs.append({"outer": outer, "position": position, "program": program,
                             "source": source, "destination": destination,
                             "input_transfer_position": left["position"], "output_transfer_position": right["position"],
                             "input_vault": left["destination"], "output_vault": right["source"],
                             "instruction": name, "pool": pool, "input_mint": left["mint"],
                             "output_mint": right["mint"], "amount_in_raw": str(amount),
                             "amount_out_raw": right["raw_amount"], "minimum_out_raw": str(minimum),
                             "verification": "INSTRUCTION_AND_TRANSFERS_MATCH"})
            except (ValueError, KeyError, TypeError, IndexError):
                unresolved.append({"outer": outer, "position": position, "program": program})
    return {"legs": legs, "unresolved": unresolved,
            "scope": "Raydium CPMM base-input, AMM base-in-v2, CLMM exact-input; reconciled fee-free Token-2022 transfers only",
            "full_route_verified": False}
