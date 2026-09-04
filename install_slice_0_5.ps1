# install_slice_0_5.ps1
# Installs Slice 0.5 - Core Contract Python Skeletons for smartmoneybotv3

param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Slice 0.5] $Message" -ForegroundColor Cyan
}

function New-DirectoryIfMissing {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    if ((Test-Path -LiteralPath $Path) -and (-not $Force)) {
        Write-Host "SKIP existing file: $Path" -ForegroundColor Yellow
        return
    }

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-DirectoryIfMissing -Path $parent
    }

    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    Write-Host "WRITE $Path" -ForegroundColor Green
}

$Root = Resolve-Path $ProjectRoot
$RootPath = $Root.Path

Write-Step "Installing Python contract skeletons into: $RootPath"

New-DirectoryIfMissing -Path (Join-Path $RootPath "src")
New-DirectoryIfMissing -Path (Join-Path $RootPath "tests")
New-DirectoryIfMissing -Path (Join-Path $RootPath "scripts")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoney")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoney\core")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoney\core\contracts")

Write-Step "Writing contract modules"

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\__init__.py") -Content @'
from .alert import AlertRecord
from .base import CoreContract
from .candle import Candle
from .context import ContextState
from .decision import DecisionRecord
from .evidence import EvidenceItem
from .risk import RiskFlag
from .setup import SetupCandidate
from .structure import StructureEvent

__all__ = [
    "AlertRecord",
    "CoreContract",
    "Candle",
    "ContextState",
    "DecisionRecord",
    "EvidenceItem",
    "RiskFlag",
    "SetupCandidate",
    "StructureEvent",
]
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\base.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CoreContract:
    schema_version: str
    contract_type: str
    id: str
    created_at: datetime
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\candle.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class Candle(CoreContract):
    market: str
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    trade_count: int | None
    source_ref: str | None
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\structure.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class StructureEvent(CoreContract):
    event_type: str
    market: str
    symbol: str
    timeframe: str
    occurred_at: datetime
    reference_level: Decimal
    direction: str
    reference_id: str
    evidence_ref: str | None
    reason_code: str | None
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\context.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class ContextState(CoreContract):
    market: str
    symbol: str
    timeframe: str
    occurred_at: datetime
    structural_bias: str
    liquidity_position: str | None
    active_imbalances: tuple[str, ...]
    active_risk_flags: tuple[str, ...]
    evidence_ref: str | None
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\setup.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class SetupCandidate(CoreContract):
    market: str
    symbol: str
    timeframe: str
    occurred_at: datetime
    setup_type: str
    status: str
    context_ref: str | None
    evidence_ref: str | None
    reason_code: str | None
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\decision.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class DecisionRecord(CoreContract):
    market: str
    symbol: str
    timeframe: str
    occurred_at: datetime
    decision_type: str
    setup_ref: str | None
    context_ref: str | None
    evidence_ref: str | None
    reason_code: str | None
    risk_flags: tuple[str, ...]
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\alert.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class AlertRecord(CoreContract):
    market: str
    symbol: str
    timeframe: str
    occurred_at: datetime
    alert_type: str
    decision_ref: str | None
    severity: str
    reason_code: str | None
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\evidence.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class EvidenceItem(CoreContract):
    occurred_at: datetime
    evidence_type: str
    source_ref: str | None
    context_ref: str | None
    details: dict[str, object] | None
    generated_by: str
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoney\core\contracts\risk.py") -Content @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base import CoreContract


@dataclass(frozen=True, slots=True)
class RiskFlag(CoreContract):
    occurred_at: datetime
    flag_type: str
    severity: str
    reason_code: str | None
    evidence_ref: str | None
'@

Write-Step "Writing tests"

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_imports.py") -Content @'
from smartmoney.core.contracts import (
    AlertRecord,
    Candle,
    ContextState,
    DecisionRecord,
    EvidenceItem,
    RiskFlag,
    SetupCandidate,
    StructureEvent,
)


def test_contracts_import() -> None:
    assert Candle.__name__ == "Candle"
    assert StructureEvent.__name__ == "StructureEvent"
    assert ContextState.__name__ == "ContextState"
    assert SetupCandidate.__name__ == "SetupCandidate"
    assert DecisionRecord.__name__ == "DecisionRecord"
    assert AlertRecord.__name__ == "AlertRecord"
    assert EvidenceItem.__name__ == "EvidenceItem"
    assert RiskFlag.__name__ == "RiskFlag"
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_dataclass_shape.py") -Content @'
from dataclasses import fields, is_dataclass

from smartmoney.core.contracts import (
    AlertRecord,
    Candle,
    ContextState,
    CoreContract,
    DecisionRecord,
    EvidenceItem,
    RiskFlag,
    SetupCandidate,
    StructureEvent,
)


def _field_names(cls: type) -> list[str]:
    return [field.name for field in fields(cls)]


def test_core_contract_is_dataclass() -> None:
    assert is_dataclass(CoreContract)
    assert CoreContract.__dataclass_params__.frozen is True


def test_candle_field_names() -> None:
    assert _field_names(Candle) == [
        "schema_version",
        "contract_type",
        "id",
        "created_at",
        "market",
        "symbol",
        "timeframe",
        "open_time",
        "close_time",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "trade_count",
        "source_ref",
    ]


def test_structure_event_field_names() -> None:
    assert _field_names(StructureEvent) == [
        "schema_version",
        "contract_type",
        "id",
        "created_at",
        "event_type",
        "market",
        "symbol",
        "timeframe",
        "occurred_at",
        "reference_level",
        "direction",
        "reference_id",
        "evidence_ref",
        "reason_code",
    ]


def test_other_contracts_are_frozen_dataclasses() -> None:
    for cls in [
        ContextState,
        SetupCandidate,
        DecisionRecord,
        AlertRecord,
        EvidenceItem,
        RiskFlag,
    ]:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
'@

Write-Step "Slice 0.5 installation complete"
Write-Host ""
Write-Host "Next commands:" -ForegroundColor White
Write-Host "  $env:PYTHONPATH = 'src'"
Write-Host "  python -m pytest" -ForegroundColor Green
'@
