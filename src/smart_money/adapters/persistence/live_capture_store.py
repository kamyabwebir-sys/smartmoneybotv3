"""Single-writer, crash-resumable raw RPC archive for bounded backfill.

Each raw response commits before analysis. The page result and cursor commit
together; an interrupted page is replayed from its durable raw responses.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


@contextmanager
def capture_lock(directory):
    """OS lock is released on process termination; the inert file may remain."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "runner.lock").open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def write_capture_report(path, result):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(_encode(result))
        stream.flush()
        os.fsync(stream.fileno())
    atomic_replace(temporary, path)


class LiveCaptureStore:
    """Use inside capture_lock. One directory belongs to one wallet/network."""

    def __init__(self, directory, wallet, network, *, clock=time.time):
        self._clock = clock
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "capture.sqlite3", timeout=0)
        try:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            if self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("capture database integrity failure")
            self.db.execute("CREATE TABLE IF NOT EXISTS records (key TEXT PRIMARY KEY, body TEXT NOT NULL, digest TEXT NOT NULL)")
            identity = {"schema": "live_capture.v1", "wallet": wallet, "network": network}
            existing = self.get("identity")
            if existing is not None and existing != identity:
                raise ValueError("capture wallet/network/schema mismatch")
            if existing is None:
                with self.db:
                    self.put("identity", identity)
                    self.put("checkpoint", {"before": None, "exhausted": False, "pages": 0})
            elif self.get("checkpoint") is None:
                raise ValueError("capture checkpoint missing")
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def get(self, key):
        row = self.db.execute("SELECT body,digest FROM records WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        body, digest = row
        if hashlib.sha256(body.encode()).hexdigest() != digest:
            raise ValueError("capture record hash mismatch")
        return json.loads(body)

    def put(self, key, value):
        body = _encode(value)
        self.db.execute("INSERT OR REPLACE INTO records VALUES (?,?,?)", (key, body, hashlib.sha256(body.encode()).hexdigest()))

    def page(self, fetcher, wallet, limit, *, mode="backfill"):
        if mode not in {"backfill", "head"}:
            raise ValueError("capture mode must be backfill or head")
        pending = self.get("pending")
        if pending is not None:
            if pending["limit"] != limit or pending.get("mode", "backfill") != mode:
                raise ValueError("resume requires the pending page limit and mode")
            return self._unprocessed(pending["response"])
        checkpoint = self.get("checkpoint")
        before = checkpoint["before"] if mode == "backfill" else None
        response = {"result": []} if mode == "backfill" and checkpoint["exhausted"] else fetcher(wallet, limit, before)
        if not isinstance(response, dict) or response.get("error") or not isinstance(response.get("result"), list):
            raise ValueError("invalid signature page")
        rows = response["result"]
        if len(rows) > limit or any(not isinstance(row, dict) or not isinstance(row.get("signature"), str) or not row["signature"].strip() for row in rows):
            raise ValueError("invalid signature page rows")
        if rows and rows[-1]["signature"] == checkpoint["before"]:
            raise ValueError("signature cursor did not advance")
        with self.db:
            self.put("pending", {"limit": limit, "mode": mode, "response": response})
        return self._unprocessed(response)

    def _unprocessed(self, response):
        return dict(response, result=[row for row in response["result"]
                                      if self.get("done:" + row["signature"]) is None])

    def transaction(self, fetcher, signature):
        cached = self.get("tx:" + signature)
        if cached is not None:
            return cached
        response = fetcher(signature)
        raw = response.get("result") if isinstance(response, dict) else None
        signatures = raw.get("transaction", {}).get("signatures", []) if isinstance(raw, dict) else []
        if not isinstance(response, dict) or response.get("error") or not signatures or signatures[0] != signature:
            raise ValueError("transaction missing or identity mismatch; checkpoint retained")
        with self.db:
            self.put("tx:" + signature, response)
        return response

    def provider_observation(self, kind, subject, fetcher):
        if not all(isinstance(value, str) and value.strip() for value in (kind, subject)):
            raise ValueError("provider observation identity must be non-empty")
        key = f"provider:{kind}:{subject}"
        cached = self.get(key)
        if cached is not None:
            return cached
        response = fetcher(subject)
        if not isinstance(response, Mapping):
            raise TypeError("provider observation must be a mapping")
        with self.db:
            self.put(key, response)
        return response

    def transactions_for_pending_page(self):
        pending = self.get("pending")
        if pending is None:
            return ()
        signatures = dict.fromkeys(row["signature"] for row in pending["response"]["result"])
        return tuple(value for signature in signatures if (value := self.get("tx:" + signature)) is not None)

    def complete(self, result):
        pending = self.get("pending")
        checkpoint = self.get("checkpoint")
        mode = pending.get("mode", "backfill")
        signatures = list(dict.fromkeys(row["signature"] for row in pending["response"]["result"]))
        complete = all(self.get("tx:" + signature) is not None for signature in signatures)
        progress = {"mode": "live_head" if mode == "head" else "historical_backfill", "page_complete": complete,
                    "before": checkpoint["before"], "pages": checkpoint["pages"],
                    "exhausted": checkpoint["exhausted"],
                    "captured_at_epoch": int(self._clock())}
        if complete:
            progress.update(before=(checkpoint["before"] if mode == "head" else signatures[-1] if signatures else checkpoint["before"]),
                            pages=checkpoint["pages"] + 1,
                            exhausted=False if mode == "head" else not signatures)
        result = dict(result, ingestion=progress)
        with self.db:
            self.put("latest_report", result)
            if complete:
                for signature in signatures:
                    self.put("done:" + signature, True)
                self.put("page:" + str(checkpoint["pages"]), {"raw": pending, "report": result})
                self.put("checkpoint", {key: progress[key] for key in ("before", "pages", "exhausted")})
                self.db.execute("DELETE FROM records WHERE key='pending'")
        return result


def read_live_capture_snapshot(directory):
    """Read and verify the latest report without mutating the archive."""
    database = Path(directory) / "capture.sqlite3"
    if not database.is_file():
        raise FileNotFoundError("live capture database is unavailable")
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("capture database integrity failure")
        rows = dict(connection.execute("SELECT key,body FROM records WHERE key IN ('identity','latest_report')"))
        if set(rows) != {"identity", "latest_report"}:
            raise ValueError("live snapshot is incomplete")
        verified = {}
        for key, body in rows.items():
            digest_row = connection.execute("SELECT digest FROM records WHERE key=?", (key,)).fetchone()
            if digest_row is None or hashlib.sha256(body.encode()).hexdigest() != digest_row[0]:
                raise ValueError("capture record hash mismatch")
            verified[key] = json.loads(body)
        return {"identity": verified["identity"], "report": verified["latest_report"]}
    finally:
        connection.close()
