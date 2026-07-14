"""Pure deterministic core for Smart Money market-structure analysis."""

from .audit import DecisionTrace, EvidenceRef, RejectReason, RuleHit, make_decision_trace
from .contracts import Candle, StructureEvent
from .ids import deterministic_id
from .replay import ReplayManifest, make_replay_manifest
from .serialization import canonical_json, canonicalize
from .time import datetime_to_canonical, ensure_utc_datetime

__all__ = [
    "Candle",
    "DecisionTrace",
    "EvidenceRef",
    "RejectReason",
    "ReplayManifest",
    "RuleHit",
    "StructureEvent",
    "canonical_json",
    "canonicalize",
    "datetime_to_canonical",
    "deterministic_id",
    "ensure_utc_datetime",
    "make_decision_trace",
    "make_replay_manifest",
]
