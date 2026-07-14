# Deterministic Assumptions v1

Status: Frozen for Slice 0.3

## Assumptions

- Inputs are closed candles only.
- Candle order is ascending by canonical time.
- Core logic has no network dependency.
- Core logic does not inspect real wall-clock time during replay.
- Same inputs plus same frozen rules must produce same outputs.
- Mutable global state is disallowed in core evaluation.
- Reporting language may vary, but deterministic truth may not.

## Boundary Implications

Allowed later:

- adapters that fetch data
- dashboards that present analysis
- AI that summarizes outputs

Not allowed in core truth generation:

- execution side effects
- live discretionary overrides
- hidden operator toggles that change semantics mid-replay
