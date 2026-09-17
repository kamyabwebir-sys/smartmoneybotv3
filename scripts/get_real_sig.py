"""Print one recent Raydium signature using the configured Solana RPC URL."""

from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.production_shadow import SolanaRPCConfig

RAYDIUM_V4_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"


def main() -> int:
    try:
        response = SolanaRPCFetcher(SolanaRPCConfig.from_env()).capture_signatures(
            RAYDIUM_V4_PROGRAM_ID, limit=1
        )
        rows = response.get("result", [])
        if rows:
            print(rows[0]["signature"])
            return 0
    except (KeyError, OSError, RuntimeError, ValueError):
        pass
    print("ERROR_RPC_UNAVAILABLE")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
