#!/usr/bin/env python3
"""Small shared file primitives for q-workflow state transactions."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import BinaryIO


class WorkflowFileLockError(RuntimeError):
    """Raised when another cooperative state writer owns the lock marker."""


def atomic_replace_bytes(path: Path, value: bytes, attempts: int = 40) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp = Path(raw_temp)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(attempts):
            try:
                os.replace(temp, path)
                return
            except PermissionError:
                if attempt + 1 == attempts:
                    raise
                time.sleep(0.05)
    finally:
        if temp.exists():
            temp.unlink()


def transaction_journal_path(lock_path: Path) -> Path:
    return lock_path.with_name(lock_path.name + ".journal.json")


def acquire_lock(path: Path, *, recovery: bool = False) -> BinaryIO:
    """Acquire one crash-released, non-blocking OS lock for a shared state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not recovery and transaction_journal_path(path).exists():
            raise WorkflowFileLockError("Unresolved state transaction; run q_workflow_manager.py task recover --yes before writing")
    except WorkflowFileLockError:
        handle.close()
        raise
    except (BlockingIOError, OSError) as exc:
        handle.close()
        raise WorkflowFileLockError(f"Another q-workflow state transaction holds {path}") from exc
    return handle


def release_lock(path: Path, descriptor: BinaryIO) -> None:
    """Release an OS lock; the reusable lock file intentionally remains."""
    try:
        descriptor.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(descriptor.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor.fileno(), fcntl.LOCK_UN)
    finally:
        descriptor.close()
