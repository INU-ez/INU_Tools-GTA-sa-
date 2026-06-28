# INU_tools.tools.profiler
#
# Lightweight aggregate profiler for long-running operator work. Use via
# the `Profiler.stage(name)` context manager — it records wall time and
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
#
# Thread-safety: `stage()` may be called concurrently from a
# ThreadPoolExecutor (e.g. TXD extract). It deliberately uses NO locks —
# the addon avoids the `threading` module per extensions.blender.org
# review. Under CPython's GIL each dict/list operation is atomic; the
# per-stage totals can at worst lose the rare concurrent increment, which
# is perfectly acceptable for a diagnostics-only tool that ships disabled
# by default. We don't need exact accounting here.

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager


class Profiler:
    """Aggregate session profiler for one long-running task.

    ``stage()`` is callable from any thread (TXD extract uses a
    ThreadPoolExecutor that hits ``stage()`` concurrently from a few
    workers). No lock is taken — see the thread-safety note at the top
    of the module.
    """

    def __init__(self, title: str, enabled: bool = True):
        self.title = title
        self.enabled = enabled
        self._start = time.perf_counter() if enabled else 0.0
        # {stage_name: {'time': total_seconds, 'count': call_count}}
        self._stages: dict[str, dict] = defaultdict(lambda: {'time': 0.0, 'count': 0})
        # Up to N slowest individual stage calls: list of (seconds, stage, note)
        self._slow: list = []
        self._slow_max = 20

    def _record_slow(self, dt: float, name: str, note: str) -> None:
        if len(self._slow) < self._slow_max:
            self._slow.append((dt, name, note))
            self._slow.sort(reverse=True)
        elif dt > self._slow[-1][0]:
            self._slow[-1] = (dt, name, note)
            self._slow.sort(reverse=True)

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
            # Track slowest individual invocations for hotspot hunting.
            self._record_slow(dt, name, note)

    def add(self, name: str, seconds: float, count: int = 1, note: str = ""):
        """Manually add a timing entry — useful when the work happened
        inside a C library call you can't easily wrap in a `with` block."""
        if not self.enabled:
            return
        s = self._stages[name]
        s['time'] += seconds
        s['count'] += count
        self._record_slow(seconds, name, note)

    def wall(self) -> float:
        """Elapsed seconds since profiler creation."""
        if not self.enabled:
            return 0.0
        return time.perf_counter() - self._start

    def format_report(self) -> str:
        """Render a readable summary — stages and hotspots."""
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

        rows = sorted(self._stages.items(), key=lambda kv: -kv[1]['time'])
        for name, st in rows:
            pct = (st['time'] / wall * 100.0) if wall > 0 else 0.0
            lines.append(
                f"{name:<32} {st['time']:>8.2f} s {st['count']:>8d} {pct:>6.1f}%")

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
