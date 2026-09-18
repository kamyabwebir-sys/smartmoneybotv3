from smart_money.domain.solana_program_registry import (
    SOLANA_DEX_SCAN_PROGRAMS,
    SOLANA_MAINNET_DEX_PROGRAMS,
    resolve_solana_dex_program,
)


def test_scan_registry_and_reverse_registry_are_consistent() -> None:
    for program_id in SOLANA_DEX_SCAN_PROGRAMS.values():
        assert program_id in SOLANA_MAINNET_DEX_PROGRAMS
        assert resolve_solana_dex_program(program_id) != "UNKNOWN"


def test_unknown_program_fails_closed() -> None:
    assert resolve_solana_dex_program("11111111111111111111111111111111") == "UNKNOWN"
