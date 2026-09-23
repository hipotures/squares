from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from squares_n12_process_cprofile import _start_worker_profile


def work(x: int) -> int:
    return x * x


if __name__ == "__main__":
    out = Path("/tmp/squares_profile_smoke_output")
    out.mkdir(exist_ok=True)
    with ProcessPoolExecutor(
        max_workers=2, initializer=_start_worker_profile, initargs=(str(out),)
    ) as pool:
        assert list(pool.map(work, range(20))) == [x * x for x in range(20)]
    print(len(list(out.glob("worker-*.pstats"))))
