"""The n=11 corner-class certificate at side 96/25 (T-031).

`certificate.json` is a byte-identical copy of the exp-220 covering retained under
`campaign/series/series-000-smoke-and-calibration/results/agenda-040/`: a weighted
fractional unavoidable-set certificate on the row domain clipped by the four corner
triangles x + y <= 1/2 at depth 1/2. It declares `variant: class` and `corner_clip: 1/2`,
so `devtools.decide_certificate` refuses it without `--corner-clip 1/2` and cannot read
it as a bound on s(11). The control test `tests/test_n11_corner_class_certificate.py`
pins the bytes to the retained file and to the digest T-031 quotes.
"""
