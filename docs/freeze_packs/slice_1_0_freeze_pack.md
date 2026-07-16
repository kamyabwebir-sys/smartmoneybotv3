# Slice 1.0 Freeze Pack — Raw Candle Ingestion Contracts

## Status

BLOCKED — Repository-grounded evidence required before implementation.

This Freeze Pack is not approved for implementation.

## Slice Label

Slice 1.0 — Raw Candle Ingestion Contracts

This is a provisional planning and review label only. It does not freeze or
approve a package name, module name, class name, contract name, contract shape,
or implementation boundary.

## Current Authorization State

No source code changes are authorized.

No test changes are authorized.

No new package or directory is authorized.

No raw candle contract shape is authorized.

This document exists only to record that Slice 1.0 cannot proceed until live
repository evidence is collected with file names and line numbers.

## Decisions Safe to Freeze

The only safe decisions are process decisions:

1. Slice 1.0 must not be implemented while this file remains BLOCKED.
2. No `src/smart_money/ingestion/` package is approved.
3. No `tests/ingestion/` package is approved.
4. No `RawCandle` model is approved.
5. No serialization API is approved.
6. No time representation is approved.
7. No OHLCV representation is approved.
8. No provenance fields are approved.
9. No validation or error behavior is approved.

## Decisions Not Yet Grounded

The following decisions require live repository citations before they can be
frozen:

- roadmap sequencing after the completed prior slices
- input canonicalization phase scope
- package or module location
- test location
- contract name and shape
- field names
- field types
- OHLCV semantics
- time semantics
- serialization semantics
- deterministic ID behavior
- provenance semantics
- validation and error behavior
- testing acceptance criteria

## Out of Scope

This document does not authorize:

- source code implementation
- test implementation
- new package boundaries
- module moves
- package renames
- broad refactoring
- exchange adapters
- network clients
- database integration
- trading execution
- order placement
- risk calculation
- ML decisioning
- analytics scoring
- reporting or UI output

## Required Evidence Before Approval Review

Before this Freeze Pack can be submitted for an explicit approval review, it
must be updated with line-numbered citations from live repository files for:

1. roadmap or build-plan sequencing
2. freeze-pack or contract-first governance
3. architecture and package-boundary rules
4. serialization conventions
5. time and ID semantics
6. validation and error conventions
7. deterministic replay assumptions
8. testing strategy

Citation format:

`path/to/file.md:line`

## Approval Is Not Automatic

Evidence collection is necessary but not sufficient for implementation
approval.

Adding citations does not automatically change this document from BLOCKED to
DRAFT or APPROVED.

After evidence collection, a separate explicit review must verify:

- that every normative decision is supported by live repository evidence
- that unsupported decisions remain unresolved
- that the proposed boundary is narrow and slice-specific
- that no source code, tests, packages, dependencies, or future architecture
  scaffolding were introduced
- that the document contains an explicit approval decision

Until that separate review records an explicit approval, this Freeze Pack
remains BLOCKED and grants no implementation authority.

## Review Requirement

A valid review packet must include:

- this file
- line-numbered excerpts from every cited live repository file
- `git status --short`
- `git diff --no-index -- NUL docs/freeze_packs/slice_1_0_freeze_pack.md`
  while the file is untracked, or the equivalent tracked-file diff after it is
  added to git
- confirmation that no files under `src/` changed
- confirmation that no files under `tests/` changed
- confirmation that no source code, tests, packages, dependencies, or future
  architecture scaffolding were introduced

## Final State

Not approved for implementation.

The only authorized next action is live repository evidence collection followed
by a separate explicit approval review.
