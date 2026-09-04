from __future__ import annotations

import asyncio

from smart_money.application.live_session_runner import DefaultLiveSessionRunner


class _HappyFetcher:
    def __call__(self, cursor):
        return {"slot": cursor + 1}
class _FailingFetcher:
    def __call__(self, cursor):
        raise RuntimeError("rate limit")
def test_live_session_runner_happy_path() -> None:
    runner = DefaultLiveSessionRunner()
    result = asyncio.run(runner.run(_HappyFetcher(), start_slot=100, max_polls=1))
    assert result.session.started_slot == 100
    assert result.checkpoint is not None
    assert result.retry_evidence is None
    assert result.replay_verified is True


def test_live_session_runner_retry_path() -> None:
    runner = DefaultLiveSessionRunner()
    result = asyncio.run(runner.run(_FailingFetcher(), start_slot=100, max_polls=1))
    assert result.session.started_slot == 100
    assert result.checkpoint is None
    assert result.retry_evidence is not None
    assert result.replay_verified is False






