"""Low-frequency, monotonic phase timing with Unix-seconds event timestamps."""
from __future__ import annotations

import time
from pathlib import Path


def timestamped(message: str, epoch: int | None = None) -> str:
    stamp = int(time.time()) if epoch is None else epoch
    return "\n".join(f"[{stamp}] {line}" for line in message.splitlines() or [""])


class PhaseJournal:
    def __init__(self, path: Path | None):
        self.path = path
        self.active: dict[str, float] = {}
        self.seconds: dict[str, float] = {}
        self.calls: dict[str, int] = {}
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, name: str, event: str) -> None:
        now = time.perf_counter()
        elapsed = None
        if event == "start":
            self.active[name] = now
        elif event == "end":
            began = self.active.pop(name, None)
            if began is not None:
                elapsed = now - began
                self.seconds[name] = self.seconds.get(name, 0.0) + elapsed
                self.calls[name] = self.calls.get(name, 0) + 1
        else:
            raise ValueError("phase event must be start or end")
        if self.path is not None:
            suffix = "" if elapsed is None else f" elapsed_s={elapsed:.6f}"
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(timestamped(f"[phase] name={name} event={event}{suffix}") + "\n")

    def summary(self) -> dict:
        return {"seconds": dict(self.seconds), "calls": dict(self.calls),
                "unfinished": sorted(self.active)}
