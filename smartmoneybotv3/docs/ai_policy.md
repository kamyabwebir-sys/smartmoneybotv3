# AI Policy

Status: Frozen for Foundation Phase

## Decision

AI is design-in-scope early.

AI implementation is deferred until deterministic foundations stabilize.

Minimal AI interfaces may be introduced before full implementation if they do not affect deterministic truth.

## Allowed AI Uses

AI may be used for:
- Persian summarization.
- Persian explanation.
- Translation.
- Report narration.
- Error explanation.
- Beginner education.
- Q&A over generated reports.
- Clarifying uncertainty.
- Making reports easier to understand.

## Forbidden AI Uses

AI must not be the authoritative source for:
- Structure events.
- Risk flags.
- Token discovery truth.
- Wallet clustering truth.
- Pump/dump-like anomaly truth.
- Trading decisions.
- Execution decisions.
- Canonical scoring.

AI must not silently create facts that are not present in deterministic evidence.

## Evidence Grounding

Every AI-visible report should be grounded in deterministic evidence.

AI outputs should reference:
- Candidate IDs.
- Risk flags.
- Evidence items.
- Source summaries.
- Unknowns.
- Confidence/severity values when present.

## AI Output Requirements

AI-generated text should:
- Be in Persian for the user.
- Be beginner-friendly.
- Explain uncertainty.
- Avoid financial advice language.
- Avoid guaranteed outcomes.
- Avoid legal accusations.
- Distinguish facts from interpretation.

## Future AI Metadata

When AI implementation starts, store:
- provider.
- model.
- prompt template version.
- input evidence hash.
- output timestamp.
- safety policy version.

## AI Boundary Statement

AI explains the system's evidence. AI does not create the system's evidence.
