$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$srcPath = Join-Path $repoRoot "src"
$previousPythonPath = $env:PYTHONPATH
$separator = [System.IO.Path]::PathSeparator

try {
    if ([string]::IsNullOrEmpty($previousPythonPath)) {
        $env:PYTHONPATH = $srcPath
    } else {
        $env:PYTHONPATH = "${srcPath}${separator}${previousPythonPath}"
    }

    Push-Location $repoRoot

    @'
from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal
import json

import contracts


EXPECTED_EXPORTS = (
    "EvidencePayload",
    "GroundedEntry",
    "IngestionResult",
    "ScoreReport",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


require(tuple(contracts.__all__) == EXPECTED_EXPORTS, "contracts.__all__ changed")

payload_a = contracts.EvidencePayload(
    source_id="VERIFY",
    evidence_type="market_structure",
    timestamp=1,
    data={"z": 2, "a": {"right": 1, "left": 0}},
)
payload_b = contracts.EvidencePayload(
    source_id="VERIFY",
    evidence_type="market_structure",
    timestamp=1,
    data={"a": {"left": 0, "right": 1}, "z": 2},
)
require(
    payload_a.get_canonical_id() == payload_b.get_canonical_id(),
    "EvidencePayload canonical identity is not deterministic",
)

instances = (
    payload_a,
    contracts.GroundedEntry(payload_a.get_canonical_id(), payload_a),
    contracts.IngestionResult(True, payload_a.get_canonical_id()),
    contracts.ScoreReport(
        score=Decimal("0"),
        reasoning="contract integrity verification",
        evidence_count=1,
        score_breakdown={"evidence_count": 1, "score": Decimal("0")},
    ),
)

checked = []
for instance in instances:
    model = type(instance)
    require(is_dataclass(model), f"{model.__name__} must remain a dataclass")
    params = getattr(model, "__dataclass_params__", None)
    require(params is not None and params.frozen, f"{model.__name__} must be frozen")
    require(hasattr(model, "__slots__"), f"{model.__name__} must use slots=True")

    field_name = next(iter(model.__dataclass_fields__))
    try:
        setattr(instance, field_name, getattr(instance, field_name))
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError(f"{model.__name__} allows mutation")

    checked.append(f"{model.__module__}.{model.__name__}")

print(
    json.dumps(
        {
            "checked_models": checked,
            "deterministic_id": payload_a.get_canonical_id(),
            "status": "PASS",
            "verifier": "contract-integrity.v1",
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
)
'@ | python -

    if ($LASTEXITCODE -ne 0) {
        throw "Contract integrity verifier failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    $env:PYTHONPATH = $previousPythonPath
}
