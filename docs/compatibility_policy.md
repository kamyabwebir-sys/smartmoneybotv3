# Compatibility Facade Policy

Status: Active

## Purpose

The repository-root Python modules are temporary import-compatibility facades.
They contain no domain, application, analytics, persistence, or provider logic.
Their only supported behavior is re-exporting the canonical objects under
`src/smart_money`.

## Supported facades

| Legacy module | Canonical module |
| --- | --- |
| `analytics_orchestrator.py` | `smart_money.application.analytics` |
| `contracts.py` | canonical Analytics, Ingestion, and Persistence contracts |
| `ledger.py` | `smart_money.adapters.persistence.json_ledger` |
| `population.py` | `smart_money.application.population` |
| `provider.py` | `smart_money.ingestion.provider` |
| `replay_engine.py` | `smart_money.application.replay` |
| `scorer.py` | `smart_money.analytics.scoring` |
| `smart_money.ingestion.ledger.EvidenceLedger` | `smart_money.application.ports.evidence_ledger` |

## Release boundary

- Compatibility facades are supported for every `0.1.x` release.
- They are not eligible for removal before version `0.2.0`.
- Removal in `0.2.0` is allowed only after all repository consumers use
  canonical imports and the compatibility contract test is intentionally
  replaced by a removal test.
- No facade may emit warnings, mutate values, wrap exceptions, change types,
  or provide behavior different from the canonical object.
- Any extension of the support window requires updating this policy before the
  release boundary changes.

## Verification

`tests/compatibility/test_legacy_facades.py` is the authoritative compatibility
contract. It verifies object identity and the public `__all__` surface for
every supported facade.

Feature and integration tests must import canonical modules. They must not
duplicate facade identity assertions.
