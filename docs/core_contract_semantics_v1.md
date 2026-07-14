# Core Contract Semantics v1

Status: Frozen for Slice 0.3

## Purpose

This document defines semantic meaning for core domain terms used by the deterministic smart money pipeline.

Pipeline scope for current foundation:

Candles -> Structure/Context -> Setup -> Decision -> Alert

This document defines meaning only. It does not define implementation details unless explicitly stated.

---

## 1. Deterministic Semantics Rule

All core decisions must be reproducible from the same ordered input candles and the same frozen rule set.

Implications:

- No random behavior
- No hidden mutable state
- No dependency on wall-clock time during replay
- No dependency on external network during core evaluation
- No AI output may override deterministic core truth

---

## 2. Candle

A candle is a closed market data interval with canonical OHLCV fields.

Mandatory semantic properties:

- A candle represents a completed interval only
- A candle is not partial
- A candle belongs to exactly one market, one symbol, and one timeframe
- A candle has one opening timestamp representing interval start
- OHLC prices and volume belong to the same interval
- Core logic consumes candles in ascending time order

Not yet defined here:

- Exact field names
- Exact serialization layout
- Exact Decimal precision policy

---

## 3. Market

A market is a canonical analytical domain in which candles and derived events are interpreted.

Examples for current roadmap:

- Solana spot-like token domain
- Robinhood external market/data domain with pending technical freeze
- Base token domain

A market identifier is analytical, not marketing text.

---

## 4. Symbol

A symbol is the canonical identifier used by the system to refer to an analyzed instrument.

Semantic rules:

- A symbol must be stable inside one replay
- A symbol must map to one market
- A symbol may be represented differently by external adapters, but core uses canonical form

---

## 5. Timeframe

A timeframe is the duration of one candle interval used by a given analysis stream.

Examples:

- 1m
- 5m
- 15m
- 1h
- 4h
- 1d

Semantic rules:

- Timeframe is part of stream identity
- Events derived from one timeframe are not interchangeable with another timeframe unless a later cross-timeframe policy explicitly says so

---

## 6. Structure

Structure is the interpreted directional organization of price action over an ordered candle stream.

Structure is not a single candle.
Structure is not sentiment.
Structure is not prediction.

Structure may include:

- swing points
- directional breaks
- change-of-character events
- displacement segments
- liquidity interactions

---

## 7. Swing High

A swing high is a locally significant high point used by the ruleset as a reference in structure evaluation.

Semantic constraints:

- It must be derived from closed candles
- It must be detectable by a frozen rule
- It is a structural reference, not merely the highest price seen in arbitrary memory

---

## 8. Swing Low

A swing low is a locally significant low point used by the ruleset as a reference in structure evaluation.

Semantic constraints mirror swing high.

---

## 9. BOS

BOS means Break of Structure.

Semantic meaning:

- A BOS is a rule-qualified break beyond a previously recognized structural reference in the direction that confirms continuation of currently interpreted structure
- BOS is not merely any wick violation
- BOS is not merely any close beyond a previous candle
- BOS requires a prior structural reference defined by the ruleset

BOS says continuation, not reversal.

---

## 10. CHOCH

CHOCH means Change of Character.

Semantic meaning:

- A CHOCH is a rule-qualified structural event indicating that the previously interpreted directional character has changed or is invalidated
- CHOCH is a candidate early shift signal, not guaranteed trend reversal
- CHOCH must reference prior structure, not arbitrary candle noise

CHOCH says character change, not necessarily full trend confirmation.

---

## 11. Sweep

A sweep is a liquidity-taking interaction where price temporarily trades beyond a meaningful reference level and then fails to continue in the same way required for a structural break.

Semantic notes:

- A sweep is not identical to BOS
- A sweep often involves rejection after taking liquidity beyond prior highs or lows
- Whether wick-only or close-based behavior qualifies is implementation-policy dependent and not frozen here yet

---

## 12. Liquidity

Liquidity in this system means analytically relevant concentration of likely resting interest around structurally meaningful price references.

Examples:

- prior swing highs
- prior swing lows
- equal highs
- equal lows
- local consolidation edges

This is an analytical concept, not direct order-book truth.

---

## 13. Liquidity Zone

A liquidity zone is a price area derived from one or more liquidity references, represented for analysis as a meaningful target or interaction region.

A liquidity zone may be exact or banded, depending on later contract freeze.

---

## 14. Displacement

Displacement is an unusually forceful price movement segment suggesting meaningful imbalance or urgency relative to surrounding structure.

Semantic notes:

- It is comparative, not absolute
- It must be defined by deterministic criteria
- It cannot rely on subjective visual judgment in final implementation

---

## 15. Imbalance

Imbalance is a directional inefficiency in recent price delivery suggesting incomplete two-sided trade interaction.

Imbalance is a broader concept.
FVG is one possible formalized subtype used by implementation.

---

## 16. FVG

FVG means Fair Value Gap.

Semantic meaning:

- FVG is a rule-defined gap-like inefficiency formed across a multi-candle relationship
- FVG is a specific formal pattern, not every fast move
- FVG belongs to the imbalance family but is narrower than imbalance in general

Exact candle formula is not frozen in Slice 0.3.

---

## 17. Context

Context is the higher-level interpretive state surrounding current price action.

Context may include:

- current structural bias
- location relative to liquidity
- displacement presence
- recent sweeps
- active imbalance regions
- higher-timeframe alignment, if enabled in later slices

Context is explanatory state, not execution instruction.

---

## 18. Setup Candidate

A setup candidate is a deterministic pattern state indicating that current conditions may justify a downstream decision evaluation.

A setup candidate is:

- not an order
- not execution permission
- not risk sizing
- not a guaranteed signal

It is an intermediate domain object between context and decision.

---

## 19. Decision

A decision is the output of deterministic rule evaluation over available setup/context evidence.

Semantic rule:

- Decision belongs to analysis, not execution
- Decision may represent classifications such as valid, invalid, watchlist, blocked, or defer
- Decision must be explainable via evidence and reason codes

---

## 20. Alert

An alert is a reporting/event output emitted after deterministic analysis determines a reportable state transition or notable condition.

An alert is not trade execution.

---

## 21. Evidence Item

An evidence item is a machine-readable justification fragment attached to a derived event, setup, or decision.

Semantic expectations:

- It must point to observable deterministic facts
- It should be stable under replay
- It should help Persian reporting and future AI explanation
- It must not contain hidden subjective judgment

Examples of evidence categories:

- structure_reference
- break_confirmation
- liquidity_interaction
- displacement_observation
- imbalance_presence
- invalidation_reason

---

## 22. Reason Code

A reason code is a stable symbolic identifier for why a decision, setup, alert, or rejection occurred.

Semantic constraints:

- Reason codes must be stable across minor refactors
- Reason codes must be concise and machine-friendly
- Human-readable Persian explanations may change, but the code should remain stable

---

## 23. Risk Flag

A risk flag is a non-execution warning marker that indicates analytical caution.

Examples:

- low_structure_confidence
- conflicting_context
- thin_history
- volatile_anomaly
- suspicious_cluster_activity

Risk flags do not perform risk management.
They annotate uncertainty or caution for reporting.

---

## 24. Token Candidate

A token candidate is a discovered or selected instrument eligible for downstream analytical evaluation.

It belongs to discovery/selection scope, not to deterministic structure truth itself.

---

## 25. Wallet Profile

A wallet profile is an analytical summary object describing observed on-chain behavior patterns for an address or address cluster.

This concept is outside the strict core structure engine and belongs to discovery/intelligence layers.

---

## 26. Suspicious Cluster

A suspicious cluster is a deterministic or rule-qualified grouping of addresses, flows, or token interactions that appears materially coordinated or anomalous.

This is a detection/reporting concept.
It does not assert criminality or intent.

---

## 27. Pump/Dump-like Anomaly

A pump/dump-like anomaly is a rule-qualified suspicious coordinated pattern involving unusual participation, price behavior, flow behavior, or concentration signatures.

Semantic constraints:

- This is an analytical label only
- It does not claim legal or factual wrongdoing
- It must be evidence-backed
- It belongs to reporting/intelligence layers, not base candle truth

---

## 28. Deterministic Replay

Deterministic replay means that re-running the same frozen engine on the same canonical input sequence yields the same derived outputs.

Same means:

- same semantic classifications
- same event ordering
- same reason codes
- same evidence content, except where later specs explicitly allow metadata differences

---

## 29. AI Role Boundary

AI may help with:

- summarization
- Persian explanation generation
- operator assistance
- document drafting

AI may not:

- redefine core truth
- inject unstated facts into deterministic decisions
- override frozen reason codes
- invent evidence

---

## 30. Out of Scope for This Semantic Freeze

Not frozen yet:

- exact candle schema
- exact swing detection algorithm
- exact BOS confirmation rule
- exact CHOCH confirmation rule
- exact sweep confirmation rule
- exact FVG formula
- exact evidence payload schema
- exact reason code registry
- exact event model fields
- exact serializer format
- exact hash construction

These belong to later slices.

---

## Slice 0.3 Patch Clarifications

Decision means analytical classification, not trading decision.

Risk flags are analytical caution labels only. They do not size positions, block capital, manage exposure, authorize execution, or perform portfolio risk management.

Robinhood is tracked only as a provisional future data/integration domain until its technical surface is validated.

A pump/dump-like anomaly must not be presented as an accusation, allegation, or proof of intent.
