# Serialization, Time, and ID Semantics v1

Status: Proposed Freeze for Slice 0.5

All timestamps must be timezone-aware UTC.

Canonical timestamp format:
YYYY-MM-DDTHH:MM:SS.ffffffZ

wall-clock reads inside core constructors are forbidden.
created_at participates in canonical serialization.
created_at does not participate in deterministic ID inputs.

Decimal values must be represented as canonical strings.
Canonical serialization uses lexicographic ordering.
Collections must be represented as ordered tuples.
Arbitrary mapping payloads are not frozen.