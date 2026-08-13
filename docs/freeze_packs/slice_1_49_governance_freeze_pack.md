# Slice 1.49 - Governance Freeze Pack

## Slice Identity
- Slice: 1.49
- Name: Consumer Evidence Ingestion
- Mode: READ_ONLY / FAIL_CLOSED
- Authority: NONE

## Purpose
این اسلایس فقط برای تعریف قرارداد حاکمیتی ingestion برای evidence مصرف‌کننده است.
هیچ تصمیم اجرایی، trading logic، risk calculation، یا opaque ML decisioning مجاز نیست.

## Protected Baseline
- Slice 0.10: Deterministic Structure Discovery Registry
- Protected files:
  - `src/smart_money/discovery/registry.py`
  - `tests/discovery/test_registry.py`

این فایل‌ها نباید تغییر کنند مگر با درخواست صریح و مستقیم برای همان slice.

## Current Context
اسلایس‌های 1.44 تا 1.48 قراردادهای governance و consumer compliance را تثبیت کرده‌اند.
Slice 1.48 به‌صورت `read_only_consumer_compliance_contract_lock` نهایی شده است.
Slice 1.49 باید بر همان مبنا، فقط قرارداد ingestion/evidence را formalize کند.

## Scope
- تعریف Freeze Pack و acceptance framing برای مصرف evidence
- حفظ determinism و replayability
- ثبت contract boundaries برای evidence ingestion
- fail-closed behavior در صورت ambiguity یا missing authority

## Out of Scope
- هرگونه execution/trading logic
- هرگونه risk calculation
- هرگونه decisioning مستقیم توسط ML
- تغییر در protected baseline
- reporting/UI leakage into core/domain logic

## Guardrails
- Deterministic
- Replayable
- Slice-scoped
- Fail-closed
- No authority escalation
- No behavior outside governance contract

## Acceptance Notes
- این slice فقط یک governance contract جدید تعریف می‌کند
- هیچ تغییر عملکردی در core/domain مجاز نیست
- هر artifact جدید باید canonical و auditable باشد

## Suggested Next Artifacts
- `install_slice_1_49.ps1`
- `slice_1_49_governance_freeze_pack.receipt.json`
- optional review/verify script for slice 1.49 governance lock
