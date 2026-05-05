# INU_tools.tools.profiler
#
# Lightweight profiler for long-running operator work. Use via the
# `Profiler.stage(name)` context manager — it records wall time and
# per-stage call count.
#
# Example:
#     p = Profiler("Extract Resources")
#     with p.stage('DFF/COL extract'):
#         img.extract_all_to(...)
#     with p.stage('TXD parse'):
#         read_txd(data)
#     print(p.format_report())
#     p.save_log("/path/to/_profile.log")
#
# The profiler is a no-op when disabled (`enabled=False`) — stage() just
# runs the wrapped block without any timing overhead. Keep it off by
# default and only flip on when diagnosing performance problems.

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager


# Single-thread workflow — see Step 7 of the extensions.blender.org
# review fixes (no `threading` per ToS). Kept as a constant so the
# `_per_thread` data shape stays identical for `format_report`.
_SINGLE_TID = 0


class Profiler:
    """Single-session profiler for one long-running task."""

    def __init__(self, title: str, enabled: bool = True):
        self.title = title
        self.enabled = enabled
        self._start = time.perf_counter() if enabled else 0.0
        # {stage_name: {'time': total_seconds, 'count': call_count}}
        self._stages: dict[str, dict] = defaultdict(lambda: {'time': 0.0, 'count': 0})
        # {stage_name: {thread_id: [total_seconds, call_count]}}
        self._per_thread: dict[str, dict] = defaultdict(
            lambda: defaultdict(lambda: [0.0, 0]))
        # Up to N slowest individual stage calls: list of (seconds, stage, note)
        self._slow: list = []
        self._slow_max = 20

    @contextmanager
    def stage(self, name: str, note: str = ""):
        """Record wall time spent inside the `with` block under `name`."""
        if not self.enabled:
            yield
            return
        t0 = time.perf_counter()
        try:
            yield
        finally:
            dt = time.perf_counter() - t0
            s = self._stages[name]
            s['time'] += dt
            s['count'] += 1
            pt = self._per_thread[name][_SINGLE_TID]
            pt[0] += dt
            pt[1] += 1
            # Track slowest individual invocations for hotspot hunting.
            if len(self._slow) < self._slow_max:
                self._slow.append((dt, name, note))
                self._slow.sort(reverse=True)
            elif dt > self._slow[-1][0]:
                self._slow[-1] = (dt, name, note)
                self._slow.sort(reverse=True)

    def add(self, name: str, seconds: float, count: int = 1, note: str = ""):
        """Manually add a timing entry — useful when the work happened
        inside a C library call you can't easily wrap in a `with` block."""
        if not self.enabled:
            return
        s = self._stages[name]
        s['time'] += seconds
        s['count'] += count
        pt = self._per_thread[name][_SINGLE_TID]
        pt[0] += seconds
        pt[1] += count
        if len(self._slow) < self._slow_max:
            self._slow.append((seconds, name, note))
            self._slow.sort(reverse=True)
        elif seconds > self._slow[-1][0]:
            self._slow[-1] = (seconds, name, note)
            self._slow.sort(reverse=True)

    def wall(self) -> float:
        """Elapsed seconds since profiler creation."""
        if not self.enabled:
            return 0.0
        return time.perf_counter() - self._start

    def format_report(self) -> str:
        """Render a readable summary — stages, parallelism, hotspots."""
        if not self.enabled:
            return f"[profiler disabled: {self.title}]"
        wall = self.wall()
        lines = []
        lines.append("=" * 64)
        lines.append(f"PROFILER: {self.title}")
        lines.append(f"Total wall time: {wall:.2f} s")
        lines.append("=" * 64)
        lines.append(f"{'Stage':<32} {'Time':>10} {'Count':>8} {'% wall':>8}")
        lines.append("-" * 64)

        with self._lock:
            rows = sorted(self._stages.items(),
                          key=lambda kv: -kv[1]['time'])
            for name, st in rows:
                pct = (st['time'] / wall * 100.0) if wall > 0 else 0.0
                lines.append(
                    f"{name:<32} {st['time']:>8.2f} s {st['count']:>8d} {pct:>6.1f}%")

            # Per-thread breakdown only where it matters — stages that
            # were hit by more than one thread (otherwise noise).
            multi_thread_stages = [
                name for name, threads in self._per_thread.items()
                if len(threads) > 1
            ]
            if multi_thread_stages:
                lines.append("")
                lines.append("Thread parallelism (stages seen from >1 thread):")
                for name in multi_thread_stages:
                    lines.append(f"  [{name}]")
                    threads = self._per_thread[name]
                    for tid, (t, n) in sorted(threads.items(),
                                              key=lambda kv: -kv[1][0]):
                        short = tid & 0xFFFF
                        lines.append(
                            f"    thread {short:>5}: {t:>6.2f} s  ({n} calls)")

            if self._slow:
                lines.append("")
                lines.append(f"Slowest {len(self._slow)} individual calls:")
                for dt, name, note in self._slow:
                    tail = f"  — {note}" if note else ""
                    lines.append(f"  {dt*1000:>7.1f} ms  [{name}]{tail}")

        lines.append("=" * 64)
        return "\n".join(lines)

    def save_log(self, path: str) -> None:
        """Append the report to a text file — keeps history across runs."""
        if not self.enabled:
            return
        try:
            with open(path, 'a', encoding='utf-8') as f:
                import datetime as _dt
                stamp = _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n\n[{stamp}]\n")
                f.write(self.format_report())
                f.write("\n")
        except Exception:
            pass

    def print_report(self) -> None:
        """Print the report to Blender's system console / stdout."""
        if not self.enabled:
            return
        print(self.format_report())
