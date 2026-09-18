from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True, slots=True)
class DiscoverySeed:
    chain: str
    subject: str

    def __post_init__(self) -> None:
        if self.chain not in {"solana", "bsc", "ethereum"} or not self.subject.strip():
            raise ValueError("unsupported or empty discovery seed")
        if self.chain == "solana" and self.subject.startswith("0x"):
            raise ValueError("EVM address cannot be used as Solana seed")
        if self.chain in {"bsc", "ethereum"} and not self.subject.startswith("0x"):
            raise ValueError("EVM seed must use 0x address format")


def scan_seed(seed: DiscoverySeed, fetch_signatures: Callable[[str], tuple[Mapping[str, Any], ...]], *, min_events: int = 1) -> tuple[dict[str, Any], ...]:
    if min_events < 1:
        raise ValueError("min_events must be positive")
    events = fetch_signatures(seed.subject)
    counts: dict[str, int] = {}
    for event in events:
        wallet = event.get("wallet") or event.get("signer")
        if isinstance(wallet, str) and wallet.strip():
            counts[wallet.strip()] = counts.get(wallet.strip(), 0) + 1
    return tuple({"wallet": wallet, "event_count": count, "chain": seed.chain} for wallet, count in sorted(counts.items()) if count >= min_events)


__all__ = ["DiscoverySeed", "scan_seed"]
