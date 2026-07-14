# Slice 0.2 Notes

Status: Installed

## Goal

Create the minimal Python project skeleton for smartmoneybotv3.

## Files Added

- pyproject.toml
- pytest.ini
- src/smartmoneybot/__init__.py
- src/smartmoneybot/governance/__init__.py
- src/smartmoneybot/core/__init__.py
- src/smartmoneybot/discovery/__init__.py
- src/smartmoneybot/adapters/__init__.py
- src/smartmoneybot/reporting/__init__.py
- src/smartmoneybot/ai/__init__.py
- tests/test_smoke_import.py
- tests/test_project_structure.py
- scripts/run_tests.ps1
- scripts/bootstrap_dev.ps1

## Acceptance Criteria

- Package import works.
- Version import works.
- pytest discovers tests.
- Foundation docs exist.
- Expected package directories exist.
- No domain logic implemented yet.
- No live network needed.

## Out Of Scope

- Domain contracts.
- Serialization.
- Core candle logic.
- Discovery logic.
- Adapters.
- Reporting models.
- AI implementation.
