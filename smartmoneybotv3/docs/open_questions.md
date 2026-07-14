# Open Questions

Status: Active

This document tracks unresolved decisions. Do not guess silently. If a question affects semantics, contracts, scoring, or external integration, resolve it here before implementation.

## Robinhood Technical Surface

Current assumption:
- Robinhood is a new Ethereum-based network/domain.
- It is provisional until validated.

Open questions:
- Is it fully EVM-compatible?
- What is the chain ID?
- What RPC providers are available?
- Is there a block explorer?
- Are token contracts standard ERC-20/ERC-721/ERC-1155?
- Are there official docs?
- Are there rate limits?
- What raw data is required for discovery?
- What is the earliest safe adapter scope?

## Base Scope

Current assumption:
- Base means the Ethereum L2 network.

Open questions:
- Which RPC provider should be used?
- Which explorer/API should be used?
- Which token standards are initially supported?
- Should Base be implemented before or after Robinhood validation?

## Solana First Scope

Open questions:
- Which data provider is preferred?
- RPC only or indexer?
- Should token discovery start from launches, DEX pools, wallets, or trending data?
- Which DEX sources are initial targets?
- Which wallet behavior patterns are first?

## Market Structure Semantics

Open questions:
- Exact definition of swing high/low.
- Exact definition of BOS.
- Exact definition of CHOCH.
- Exact definition of sweep.
- Exact definition of liquidity zone.
- Exact definition of FVG/imbalance.
- Which candle timestamp represents the candle: open time or close time?
- Which timeframes are initially supported?

## Token Discovery

Open questions:
- What makes a token candidate?
- What minimum data is required?
- How is source reliability represented?
- How are scams/rug risks flagged?
- How are missing data and unknowns reported?

## Wallet Intelligence

Open questions:
- What makes a wallet "smart"?
- What evidence is required before labeling?
- How is wallet confidence calculated?
- How are related wallets detected?
- How are clusters represented?
- How are false positives reduced?

## Pump/Dump-Like Anomaly Analysis

Open questions:
- What thresholds define abnormal price/volume behavior?
- What wallet-flow timing is suspicious?
- How should liquidity exit patterns be represented?
- How should concentration changes be measured?
- How should coordinated-looking behavior be reported without overclaiming?

## Reporting

Open questions:
- What report sections are required for beginners?
- What risk levels are used?
- Should reports include recommended next actions?
- What disclaimers are required?
- How detailed should Telegram summaries be?
- What dashboard widgets are first?

## AI

Open questions:
- Which model provider is used later?
- Should the first AI interface be local, cloud, or provider-agnostic?
- What evidence format is passed to AI?
- How are AI outputs audited?
- Should AI output be stored with prompt/model/version metadata?

## Infrastructure

Open questions:
- Is SQLite enough for early local storage?
- Should DuckDB be used for analytical snapshots?
- When should a server database be introduced?
- Which job runner is acceptable on Windows?
- Which deployment target is first on Linux?
