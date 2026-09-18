# Real trending-token purchase sample (not yet production-decoder accepted)

Discovery source: gmgn-cli market trending --chain sol --interval 1h
--order-by volume --limit 5 --raw. LinkedInu was rank 5 in the returned filtered
list, with reported hourly volume 590338 USD, liquidity 15241.4 USD and rug_ratio
0.248. These are transient vendor observations, not a safety endorsement.

Token: mMHUFPJma7sGuFxYteoHJkfzb5iW6oLxsvVnUYfSTNK
Wallet: 2FRFWM24vDbdCfs7k6at3dqtNKDVHghdZ1d6zmw5w2S2
Signature: 4TGjPYbtGWPT8G7WvZi27CEc4Pq8jVT5T45nC61qsuq2AaTte63dXPWNbAAju9vqgTegHoQEHFFKKmwr2B6KfEv2
Slot: 447649596. blockTime: 1789601994. RPC meta.err: null.

Raw RPC response: fixtures/solana/mainnet/s12-trending-buy-candidate.json

Owner-level movements (integer balances and parsed transfers reconciled):
- USDC: -9486854 raw at 6 decimals = -9.486854 USDC.
- XspzcW1PRtgf6Wj92HCiZdjzKCyFekVD8P5Ueh3dRMX: 1902634 raw in and out;
  8 decimals; net zero (intermediate).
- LinkedInu: +305853508248 raw at 6 decimals = +305853.508248 tokens;
  no outgoing transfer of this mint for this wallet in the transaction.
- Native SOL: fee-adjusted delta zero; fee 10825 lamports.

Parsed USDC transfers: 9439420 raw to swap vault, plus 47434 raw separate
transfer in the Jupiter instruction. The latter's recipient purpose has not been
independently verified; do not label it a particular fee type by guesswork.
Observed call sequence: Jupiter -> Raydium CLMM -> Raydium CPMM,
with USDC -> intermediate token -> target token flow.

This is evidence of a completed directional purchase, not proof of smart-money
skill, future returns, safety, or that the buyer is human.
Existing decoder returns no verified legs: CLMM is unsupported and CPMM rejects
Token-2022 semantics. ranking_eligible remains false. No production acceptance
logic or tests were changed. Next work is CLMM/Token-2022 decoding with positive
and adversarial regression tests, not a manual bypass of the gate.
