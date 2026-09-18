from __future__ import annotations

from pathlib import Path

from smart_money.adapters.persistence import atomic_file


def test_atomic_replace_syncs_destination_parent_when_supported(
    monkeypatch,
) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        atomic_file,
        "_directory_fsync_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        atomic_file.os,
        "replace",
        lambda source, target: calls.append(("replace", (source, target))),
    )
    monkeypatch.setattr(
        atomic_file.os,
        "open",
        lambda path, flags: calls.append(("open", (path, flags))) or 7,
    )
    monkeypatch.setattr(
        atomic_file.os,
        "fsync",
        lambda descriptor: calls.append(("fsync", descriptor)),
    )
    monkeypatch.setattr(
        atomic_file.os,
        "close",
        lambda descriptor: calls.append(("close", descriptor)),
    )

    atomic_file.atomic_replace(
        Path("state.json.tmp"),
        Path("nested/state.json"),
    )

    assert calls[0] == (
        "replace",
        (Path("state.json.tmp"), Path("nested/state.json")),
    )
    assert calls[1][0] == "open"
    assert calls[1][1][0] == "nested"
    assert calls[2:] == [("fsync", 7), ("close", 7)]


def test_atomic_replace_skips_directory_sync_when_unsupported(
    monkeypatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        atomic_file,
        "_directory_fsync_supported",
        lambda: False,
    )
    monkeypatch.setattr(
        atomic_file.os,
        "replace",
        lambda source, target: calls.append("replace"),
    )
    monkeypatch.setattr(
        atomic_file.os,
        "open",
        lambda path, flags: calls.append("open"),
    )

    atomic_file.atomic_replace("state.json.tmp", "state.json")

    assert calls == ["replace"]
