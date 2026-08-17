from __future__ import annotations

import os
from pathlib import Path


def _directory_fsync_supported() -> bool:
    return os.name != "nt"


def _sync_parent_directory(path: Path) -> None:
    if not _directory_fsync_supported():
        return
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(os.fspath(path), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_replace(
    temporary_path: str | os.PathLike[str],
    destination_path: str | os.PathLike[str],
) -> None:
    """Replace one file and durably retain its directory entry on POSIX."""
    temporary = Path(temporary_path)
    destination = Path(destination_path)
    os.replace(temporary, destination)
    _sync_parent_directory(destination.parent)


__all__ = ["atomic_replace"]
