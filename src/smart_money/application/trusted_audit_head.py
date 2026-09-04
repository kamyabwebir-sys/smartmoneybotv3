from __future__ import annotations

import hmac
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from smart_money.application._validation import (
    StableCollectionSnapshot,
    assert_stable_collection_snapshot,
    take_stable_collection_snapshot,
)
from smart_money.application._validation import (
    require_count as _require_count,
)
from smart_money.application._validation import (
    require_sha256 as _require_sha256,
)
from smart_money.application._validation import (
    require_text as _require_text,
)
from smart_money.application.ports.historical_audit_manifest_store import (
    HistoricalAuditManifestStore,
)
from smart_money.core.ids import deterministic_id

_HEAD_SCHEMA_VERSION = "trusted_audit_head.v1"
_VERIFICATION_SCHEMA_VERSION = "trusted_audit_head_verification.v1"


class TrustedAuditHeadStatus(str, Enum):
    CURRENT = "CURRENT"
    ADVANCE_REQUIRED = "ADVANCE_REQUIRED"
    ROLLBACK = "ROLLBACK"
    DIVERGED = "DIVERGED"


@runtime_checkable
class PrefixVerifiableHistoricalAuditStore(
    HistoricalAuditManifestStore,
    Protocol,
):
    def contains_content_hash(
        self,
        content_hash: str,
        manifest_count: int,
    ) -> bool:
        """Return whether a count/hash pair identifies a canonical prefix."""
        ...


@dataclass(frozen=True, slots=True)
class TrustedAuditHead:
    """Trusted monotonic anchor for one historical manifest-store prefix."""

    anchor_id: str
    manifest_store_hash: str
    manifest_count: int
    latest_audit_id: str | None
    previous_anchor_id: str | None
    schema_version: str = _HEAD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "anchor_id",
            _require_text(self.anchor_id, "anchor_id"),
        )
        object.__setattr__(
            self,
            "manifest_store_hash",
            _require_sha256(
                self.manifest_store_hash,
                "manifest_store_hash",
            ),
        )
        object.__setattr__(
            self,
            "manifest_count",
            _require_count(self.manifest_count, "manifest_count"),
        )
        for field_name in ("latest_audit_id", "previous_anchor_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_text(value, field_name),
                )
        if (self.manifest_count == 0) != (self.latest_audit_id is None):
            raise ValueError(
                "latest_audit_id presence must agree with manifest_count"
            )
        if self.schema_version != _HEAD_SCHEMA_VERSION:
            raise ValueError("unsupported trusted audit head schema_version")
        expected_id = deterministic_id(
            "trusted_audit_head",
            self.identity_payload(),
        )
        if self.anchor_id != expected_id:
            raise ValueError("anchor_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "latest_audit_id": self.latest_audit_id,
            "manifest_count": self.manifest_count,
            "manifest_store_hash": self.manifest_store_hash,
            "previous_anchor_id": self.previous_anchor_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"anchor_id": self.anchor_id, **self.identity_payload()}


@runtime_checkable
class TrustedAuditHeadStore(Protocol):
    def save(self, head: TrustedAuditHead) -> str:
        """Persist a monotonic trusted head and return its identity."""
        ...

    def load(self) -> TrustedAuditHead:
        """Load and validate the current trusted head."""
        ...


@dataclass(frozen=True, slots=True)
class TrustedAuditHeadVerification:
    verification_id: str
    anchor_id: str
    status: TrustedAuditHeadStatus
    current_store_hash: str
    current_manifest_count: int
    current_latest_audit_id: str | None
    schema_version: str = _VERIFICATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "verification_id",
            _require_text(self.verification_id, "verification_id"),
        )
        object.__setattr__(
            self,
            "anchor_id",
            _require_text(self.anchor_id, "anchor_id"),
        )
        if not isinstance(self.status, TrustedAuditHeadStatus):
            raise TypeError("status must be a TrustedAuditHeadStatus")
        object.__setattr__(
            self,
            "current_store_hash",
            _require_sha256(
                self.current_store_hash,
                "current_store_hash",
            ),
        )
        object.__setattr__(
            self,
            "current_manifest_count",
            _require_count(
                self.current_manifest_count,
                "current_manifest_count",
            ),
        )
        if self.current_latest_audit_id is not None:
            object.__setattr__(
                self,
                "current_latest_audit_id",
                _require_text(
                    self.current_latest_audit_id,
                    "current_latest_audit_id",
                ),
            )
        if (self.current_manifest_count == 0) != (
            self.current_latest_audit_id is None
        ):
            raise ValueError(
                "current latest audit presence must agree with count"
            )
        if self.schema_version != _VERIFICATION_SCHEMA_VERSION:
            raise ValueError(
                "unsupported trusted audit verification schema_version"
            )
        expected_id = deterministic_id(
            "trusted_audit_head_verification",
            self.identity_payload(),
        )
        if self.verification_id != expected_id:
            raise ValueError(
                "verification_id does not match deterministic payload"
            )

    def identity_payload(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "current_latest_audit_id": self.current_latest_audit_id,
            "current_manifest_count": self.current_manifest_count,
            "current_store_hash": self.current_store_hash,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {
            "verification_id": self.verification_id,
            **self.identity_payload(),
        }


class TrustedAuditHeadVerificationError(RuntimeError):
    def __init__(self, verification: TrustedAuditHeadVerification) -> None:
        self.verification = verification
        super().__init__(
            "trusted audit head verification failed: "
            f"{verification.status.value}"
        )


def _snapshot_store(
    manifest_store: PrefixVerifiableHistoricalAuditStore,
) -> tuple[str, int, str | None]:
    snapshot = take_stable_collection_snapshot(
        name="manifest store",
        get_content_hash=lambda: manifest_store.content_hash,
        get_count=lambda: manifest_store.manifest_count,
        iterate=manifest_store.iter_manifests,
        identity=lambda manifest: manifest.audit_id,
        lookup=manifest_store.get,
    )
    for manifest in snapshot.items:
        if manifest.rejected_count:
            raise ValueError(
                "trusted audit head cannot anchor a rejected manifest"
            )
    latest_audit_id = (
        None if not snapshot.items else snapshot.items[-1].audit_id
    )
    return snapshot.content_hash, snapshot.count, latest_audit_id


def verify_trusted_audit_head(
    *,
    head: TrustedAuditHead,
    manifest_store: PrefixVerifiableHistoricalAuditStore,
) -> TrustedAuditHeadVerification:
    if not isinstance(head, TrustedAuditHead):
        raise TypeError("head must be a TrustedAuditHead")
    if not isinstance(manifest_store, PrefixVerifiableHistoricalAuditStore):
        raise TypeError("manifest_store must support prefix verification")

    store_hash, manifest_count, latest_audit_id = _snapshot_store(
        manifest_store
    )
    prefix_found = manifest_store.contains_content_hash(
        head.manifest_store_hash,
        head.manifest_count,
    )
    assert_stable_collection_snapshot(
        StableCollectionSnapshot(
            content_hash=store_hash,
            count=manifest_count,
            items=(),
        ),
        name="manifest store",
        get_content_hash=lambda: manifest_store.content_hash,
        get_count=lambda: manifest_store.manifest_count,
    )

    if manifest_count < head.manifest_count:
        status = TrustedAuditHeadStatus.ROLLBACK
    elif not prefix_found:
        status = TrustedAuditHeadStatus.DIVERGED
    elif manifest_count > head.manifest_count:
        status = TrustedAuditHeadStatus.ADVANCE_REQUIRED
    elif (
        hmac.compare_digest(store_hash, head.manifest_store_hash)
        and latest_audit_id == head.latest_audit_id
    ):
        status = TrustedAuditHeadStatus.CURRENT
    else:
        status = TrustedAuditHeadStatus.DIVERGED

    payload: dict[str, object] = {
        "anchor_id": head.anchor_id,
        "current_latest_audit_id": latest_audit_id,
        "current_manifest_count": manifest_count,
        "current_store_hash": store_hash,
        "schema_version": _VERIFICATION_SCHEMA_VERSION,
        "status": status.value,
    }
    return TrustedAuditHeadVerification(
        verification_id=deterministic_id(
            "trusted_audit_head_verification",
            payload,
        ),
        anchor_id=head.anchor_id,
        status=status,
        current_store_hash=store_hash,
        current_manifest_count=manifest_count,
        current_latest_audit_id=latest_audit_id,
    )


def verify_trusted_audit_head_or_raise(
    *,
    head: TrustedAuditHead,
    manifest_store: PrefixVerifiableHistoricalAuditStore,
) -> TrustedAuditHeadVerification:
    verification = verify_trusted_audit_head(
        head=head,
        manifest_store=manifest_store,
    )
    if verification.status is not TrustedAuditHeadStatus.CURRENT:
        raise TrustedAuditHeadVerificationError(verification)
    return verification


def make_trusted_audit_head(
    *,
    manifest_store: PrefixVerifiableHistoricalAuditStore,
    previous_head: TrustedAuditHead | None = None,
) -> TrustedAuditHead:
    if not isinstance(manifest_store, PrefixVerifiableHistoricalAuditStore):
        raise TypeError("manifest_store must support prefix verification")
    if previous_head is not None:
        if not isinstance(previous_head, TrustedAuditHead):
            raise TypeError("previous_head must be a TrustedAuditHead")
        verification = verify_trusted_audit_head(
            head=previous_head,
            manifest_store=manifest_store,
        )
        if verification.status is TrustedAuditHeadStatus.CURRENT:
            return previous_head
        if verification.status is not TrustedAuditHeadStatus.ADVANCE_REQUIRED:
            raise TrustedAuditHeadVerificationError(verification)
        store_hash = verification.current_store_hash
        manifest_count = verification.current_manifest_count
        latest_audit_id = verification.current_latest_audit_id
    else:
        store_hash, manifest_count, latest_audit_id = _snapshot_store(
            manifest_store
        )
    payload: dict[str, object] = {
        "latest_audit_id": latest_audit_id,
        "manifest_count": manifest_count,
        "manifest_store_hash": store_hash,
        "previous_anchor_id": (
            None if previous_head is None else previous_head.anchor_id
        ),
        "schema_version": _HEAD_SCHEMA_VERSION,
    }
    return TrustedAuditHead(
        anchor_id=deterministic_id("trusted_audit_head", payload),
        manifest_store_hash=store_hash,
        manifest_count=manifest_count,
        latest_audit_id=latest_audit_id,
        previous_anchor_id=payload["previous_anchor_id"],  # type: ignore[arg-type]
    )


def advance_trusted_audit_head(
    *,
    manifest_store: PrefixVerifiableHistoricalAuditStore,
    head_store: TrustedAuditHeadStore,
) -> TrustedAuditHead:
    if not isinstance(head_store, TrustedAuditHeadStore):
        raise TypeError("head_store must satisfy TrustedAuditHeadStore")
    try:
        previous_head = head_store.load()
    except FileNotFoundError:
        previous_head = None
    head = make_trusted_audit_head(
        manifest_store=manifest_store,
        previous_head=previous_head,
    )
    persisted_id = head_store.save(head)
    if persisted_id != head.anchor_id:
        raise RuntimeError("trusted head store returned a mismatched identity")
    if head_store.load() != head:
        raise RuntimeError("trusted head store did not retain the saved head")
    verify_trusted_audit_head_or_raise(
        head=head,
        manifest_store=manifest_store,
    )
    return head


__all__ = [
    "PrefixVerifiableHistoricalAuditStore",
    "TrustedAuditHead",
    "TrustedAuditHeadStatus",
    "TrustedAuditHeadStore",
    "TrustedAuditHeadVerification",
    "TrustedAuditHeadVerificationError",
    "advance_trusted_audit_head",
    "make_trusted_audit_head",
    "verify_trusted_audit_head",
    "verify_trusted_audit_head_or_raise",
]
