"""Supervise repeated read-only discovery sessions and persist operational metrics."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def _rss_bytes(process: subprocess.Popen) -> int | None:
    if os.name != "nt":
        status = Path(f"/proc/{process.pid}/status")
        if status.is_file():
            for line in status.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
        return None
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    handle = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x0400, False, process.pid)
    if not handle:
        return None
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        return int(counters.WorkingSetSize) if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb) else None
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _append_metric(path: Path, metric: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(metric, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuous read-only shadow production supervisor")
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--cycles", type=int, default=0, help="0 means run until interrupted")
    parser.add_argument("--interval-seconds", type=float, default=30)
    parser.add_argument("--max-rss-mb", type=int, default=512)
    args = parser.parse_args()
    if args.cycles < 0 or not 1 <= args.limit <= 1000 or args.interval_seconds < 1 or args.max_rss_mb < 32:
        parser.error("invalid bounded shadow settings")
    cycle = failures = 0
    try:
        while args.cycles == 0 or cycle < args.cycles:
            cycle += 1
            command = [sys.executable, str(Path(__file__).with_name("live_rpc_runner.py")),
                       "--wallet", args.wallet, "--limit", str(args.limit), "--pages", "1",
                       "--state-dir", str(args.state_dir), "--output", str(args.output),
                       "--enrich-safety-funding", "--mode", "head"]
            started = time.monotonic()
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            peak_rss = 0
            while process.poll() is None:
                sample = _rss_bytes(process)
                peak_rss = max(peak_rss, sample or 0)
                time.sleep(0.05)
            stdout, _stderr = process.communicate()
            report = {}
            try:
                report = json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else {}
            except json.JSONDecodeError:
                pass
            failed = process.returncode not in {0, 2}
            failures += int(failed)
            metric = {
                "schema_version": "shadow_cycle_metric.v1", "cycle": cycle,
                "elapsed_ms": int((time.monotonic() - started) * 1000),
                "exit_code": process.returncode, "failed": failed,
                "peak_rss_bytes": peak_rss or None,
                "rss_budget_exceeded": bool(peak_rss and peak_rss > args.max_rss_mb * 1024 * 1024),
                "rpc": report.get("operational_metrics", {}),
                "page_complete": report.get("ingestion", {}).get("page_complete"),
                "archive_bytes": sum(item.stat().st_size for item in args.state_dir.glob("capture.sqlite3*")),
                "error_class": "runner_failed" if failed else None,
            }
            _append_metric(args.metrics, metric)
            if metric["rss_budget_exceeded"]:
                return 3
            if args.cycles == 0 or cycle < args.cycles:
                time.sleep(args.interval_seconds)
    except KeyboardInterrupt:
        return 130
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
