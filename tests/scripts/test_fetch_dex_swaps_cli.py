import pytest

from scripts.fetch_dex_swaps import main, parse_options


def test_cli_dry_run_without_wallet_or_rpc_environment(capsys) -> None:
    assert main(["--dry-run"]) == 0
    assert "raydium_amm" in capsys.readouterr().out


def test_cli_rejects_invalid_wallet() -> None:
    with pytest.raises(SystemExit) as caught:
        parse_options(["--dry-run", "--wallet", "invalid"])
    assert caught.value.code == 2
