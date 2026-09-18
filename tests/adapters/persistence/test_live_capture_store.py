import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from smart_money.adapters.persistence.live_capture_store import (
    LiveCaptureStore,
    capture_lock,
)


def response(signature):
    return {"result": {"transaction": {"signatures": [signature]}}}


def test_interrupted_page_reuses_raw_and_commits_cursor(tmp_path):
    calls = []
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        page = {"result": [{"signature": "a"}, {"signature": "a"}, {"signature": "b"}]}
        store.page(lambda *args: page, "wallet", 3)
        store.transaction(response, "a")
        store.close()  # interruption after durable raw, before checkpoint
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        assert store.page(lambda *args: pytest.fail("refetched page"), "wallet", 3) == page
        assert store.transaction(lambda sig: pytest.fail("refetched raw"), "a") == response("a")
        assert not store.complete({})["ingestion"]["page_complete"]
        assert store.get("checkpoint")["before"] is None
        store.transaction(lambda sig: calls.append(sig) or response(sig), "b")
        assert store.complete({})["ingestion"]["before"] == "b"
        assert calls == ["b"]
        assert store.db.execute("SELECT count(*) FROM records WHERE key LIKE 'tx:%'").fetchone()[0] == 2
        store.close()


def test_corruption_identity_and_single_writer_fail_closed(tmp_path):
    with capture_lock(tmp_path):
        with pytest.raises(OSError), capture_lock(tmp_path):
            pass
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        store.transaction(response, "a")
        with store.db:
            store.db.execute("UPDATE records SET body=? WHERE key='tx:a'", (json.dumps(response("b")),))
        with pytest.raises(ValueError, match="hash"):
            store.transaction(response, "a")
        store.close()
        with pytest.raises(ValueError, match="mismatch"):
            LiveCaptureStore(tmp_path, "other", "mainnet-beta")


def test_null_and_wrong_identity_are_not_checkpointed(tmp_path):
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        store.page(lambda *args: {"result": [{"signature": "a"}]}, "wallet", 1)
        for raw in ({"result": None}, response("wrong")):
            with pytest.raises(ValueError):
                store.transaction(lambda sig, raw=raw: raw, "a")
        assert not store.complete({})["ingestion"]["page_complete"]
        assert store.get("checkpoint")["before"] is None
        store.close()


def test_page_and_checkpoint_rollback_together(tmp_path):
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        store.page(lambda *args: {"result": [{"signature": "a"}]}, "wallet", 1)
        store.transaction(response, "a")
        original = store.put

        def interrupted(key, value):
            if key == "checkpoint":
                raise OSError("injected crash")
            original(key, value)

        store.put = interrupted
        with pytest.raises(OSError):
            store.complete({})
        store.close()
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        assert store.get("page:0") is None
        assert store.get("pending") is not None
        assert store.get("checkpoint")["before"] is None
        assert store.complete({})["ingestion"]["before"] == "a"
        store.close()


def test_process_termination_keeps_raw_and_releases_lock(tmp_path):
    code = """
import os, sys
from smart_money.adapters.persistence.live_capture_store import LiveCaptureStore, capture_lock
with capture_lock(sys.argv[1]):
    store = LiveCaptureStore(sys.argv[1], 'wallet', 'mainnet-beta')
    store.page(lambda *args: {'result': [{'signature': 'a'}]}, 'wallet', 1)
    store.transaction(lambda sig: {'result': {'transaction': {'signatures': [sig]}}}, 'a')
    os._exit(7)
"""
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[3] / "src"))
    process = subprocess.run([sys.executable, "-c", code, str(tmp_path)], env=env, capture_output=True, timeout=15, check=False)
    assert process.returncode == 7
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        assert store.get("checkpoint")["before"] is None
        assert store.transaction(lambda sig: pytest.fail("network called"), "a") == response("a")
        assert store.complete({})["ingestion"]["page_complete"]
        store.close()


def test_overlapping_pages_do_not_duplicate_processing(tmp_path):
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        store.page(lambda *args: {"result": [{"signature": "a"}]}, "wallet", 2)
        store.transaction(response, "a")
        store.complete({})
        page = store.page(lambda *args: {"result": [{"signature": "a"}, {"signature": "b"}]}, "wallet", 2)
        assert page["result"] == [{"signature": "b"}]
        store.transaction(response, "b")
        store.complete({})
        assert store.db.execute("SELECT count(*) FROM records WHERE key LIKE 'done:%'").fetchone()[0] == 2
        store.close()


def test_provider_observation_is_cached_and_pending_transactions_are_available(tmp_path):
    calls = []
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        store.page(lambda *args: {"result": [{"signature": "a"}]}, "wallet", 1)
        store.transaction(response, "a")
        first = store.provider_observation("safety", "mint", lambda mint: calls.append(mint) or {"mint": mint})
        second = store.provider_observation("safety", "mint", lambda mint: pytest.fail("provider called twice"))
        assert first == second == {"mint": "mint"}
        assert calls == ["mint"]
        assert store.transactions_for_pending_page() == (response("a"),)
        store.close()


def test_head_mode_polls_again_and_processes_only_new_signatures(tmp_path):
    pages = iter(({"result": [{"signature": "a"}]}, {"result": [{"signature": "b"}, {"signature": "a"}]}))
    with capture_lock(tmp_path):
        store = LiveCaptureStore(tmp_path, "wallet", "mainnet-beta")
        assert store.page(lambda *args: next(pages), "wallet", 2, mode="head")["result"] == [{"signature": "a"}]
        store.transaction(response, "a")
        assert store.complete({})["ingestion"]["mode"] == "live_head"
        assert not store.get("checkpoint")["exhausted"]
        assert store.page(lambda *args: next(pages), "wallet", 2, mode="head")["result"] == [{"signature": "b"}]
        store.transaction(response, "b")
        store.complete({})
        assert store.db.execute("SELECT count(*) FROM records WHERE key LIKE 'done:%'").fetchone()[0] == 2
        store.close()
