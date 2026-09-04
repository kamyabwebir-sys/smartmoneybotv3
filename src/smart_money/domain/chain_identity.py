from __future__ import annotations

from dataclasses import dataclass

from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import ChainId

_EVM_NETWORKS = {"8453": "base", "4663": "robinhood-l2"}
_EVM_REFERENCES = {value: key for key, value in _EVM_NETWORKS.items()}


def canonical_chain_namespace(chain: ChainId) -> str:
    if not isinstance(chain, ChainId):
        raise TypeError("chain must be a ChainId")
    if chain.namespace == "eip155":
        return f"evm:{_EVM_NETWORKS.get(chain.reference, chain.reference)}"
    return f"{chain.namespace}:{chain.reference}"


def canonical_identity_namespace(chain: ChainId, address: str) -> str:
    normalized = _address(
        address,
        "address",
        case_sensitive=chain.namespace == "solana",
    )
    return f"{canonical_chain_namespace(chain)}:{normalized}"


@dataclass(frozen=True, slots=True)
class ParsedIdentityNamespace:
    kind: str
    chain: ChainId | None
    address: str
    legacy: bool


@dataclass(frozen=True, slots=True)
class IdentityConflict:
    code: str
    left: str
    right: str
    blocking: bool = True


def detect_identity_conflict(
    left: ParsedIdentityNamespace,
    right: ParsedIdentityNamespace,
) -> IdentityConflict | None:
    if not isinstance(left, ParsedIdentityNamespace) or not isinstance(
        right, ParsedIdentityNamespace
    ):
        raise TypeError("identities must be parsed namespaces")
    if left.kind != right.kind:
        return IdentityConflict("kind_mismatch", left.kind, right.kind)
    if left.legacy or right.legacy:
        if left.address != right.address:
            return IdentityConflict("legacy_identity_mismatch", left.address, right.address)
        return None
    if left.chain != right.chain:
        return IdentityConflict(
            "chain_mismatch",
            canonical_identity_namespace(left.chain, left.address),
            canonical_identity_namespace(right.chain, right.address),
        )
    if left.address != right.address:
        return IdentityConflict("address_collision", left.address, right.address)
    return None


def parse_identity_namespace(value: object, *, kind: str) -> ParsedIdentityNamespace:
    if not isinstance(value, str) or not value.strip():
        raise TypeError("identity namespace must be a non-empty string")
    if kind not in {"wallet", "token", "pool"}:
        raise ValueError("unsupported identity kind")
    parts = value.strip().split(":")
    if len(parts) == 3:
        family, reference, address = parts
        if family == "evm":
            reference = _EVM_REFERENCES.get(reference, reference)
            chain = ChainId("eip155", reference)
        else:
            chain = ChainId(family, reference)
        normalized = _address(
            address,
            "address",
            case_sensitive=chain.namespace == "solana",
        )
        if canonical_identity_namespace(chain, normalized) != value.strip():
            raise ValueError("identity namespace is not canonical")
        return ParsedIdentityNamespace(kind, chain, normalized, False)
    if len(parts) in {1, 2}:
        return ParsedIdentityNamespace(kind, None, value.strip(), True)
    raise ValueError("identity namespace must be canonical or legacy")


def _address(value: object, field_name: str, *, case_sensitive: bool) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized or any(character.isspace() for character in normalized):
        raise ValueError(f"{field_name} must be non-empty without whitespace")
    return normalized if case_sensitive else normalized.lower()


@dataclass(frozen=True, slots=True)
class WalletId:
    chain: ChainId
    address: str
    schema_version: str = "wallet_id.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        object.__setattr__(
            self,
            "address",
            _address(
                self.address,
                "address",
                case_sensitive=self.chain.namespace == "solana",
            ),
        )
        if self.schema_version != "wallet_id.v1":
            raise ValueError("unsupported WalletId schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "chain": self.chain.canonical_dict(),
            "schema_version": self.schema_version,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("wallet", self.canonical_dict())

    @property
    def namespace(self) -> str:
        return canonical_identity_namespace(self.chain, self.address)


@dataclass(frozen=True, slots=True)
class TokenId:
    chain: ChainId
    address: str
    schema_version: str = "token_id.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        object.__setattr__(
            self,
            "address",
            _address(
                self.address,
                "address",
                case_sensitive=self.chain.namespace == "solana",
            ),
        )
        if self.schema_version != "token_id.v1":
            raise ValueError("unsupported TokenId schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "chain": self.chain.canonical_dict(),
            "schema_version": self.schema_version,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("token", self.canonical_dict())

    @property
    def namespace(self) -> str:
        return canonical_identity_namespace(self.chain, self.address)


@dataclass(frozen=True, slots=True)
class PoolId:
    chain: ChainId
    address: str
    token0: TokenId
    token1: TokenId
    schema_version: str = "pool_id.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        if not isinstance(self.token0, TokenId) or not isinstance(
            self.token1, TokenId
        ):
            raise TypeError("pool tokens must be TokenId values")
        if self.token0.chain != self.chain or self.token1.chain != self.chain:
            raise ValueError("pool tokens must belong to the pool chain")
        if self.token0.canonical_id == self.token1.canonical_id:
            raise ValueError("pool tokens must be distinct")
        object.__setattr__(
            self,
            "address",
            _address(
                self.address,
                "address",
                case_sensitive=self.chain.namespace == "solana",
            ),
        )
        if self.schema_version != "pool_id.v1":
            raise ValueError("unsupported PoolId schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "chain": self.chain.canonical_dict(),
            "schema_version": self.schema_version,
            "token0": self.token0.canonical_dict(),
            "token1": self.token1.canonical_dict(),
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("pool", self.canonical_dict())

    @property
    def namespace(self) -> str:
        return canonical_identity_namespace(self.chain, self.address)


__all__ = [
    "ParsedIdentityNamespace",
    "IdentityConflict",
    "PoolId",
    "TokenId",
    "WalletId",
    "canonical_chain_namespace",
    "canonical_identity_namespace",
    "parse_identity_namespace",
    "detect_identity_conflict",
]
