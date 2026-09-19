#!/usr/bin/env bash
# Sequential first-wave covering waiter for session-140.
# One core. Skips a probe whose run JSON already exists. Stops at STOP_AT
# or when a freeze file appears (mass is decided by the coordinator, not here).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PACKING="$(cd "$ROOT/../../../../.." && pwd)"
STOP_AT="${STOP_AT:-2026-09-19T06:42:00Z}"
LOG="$ROOT/first-wave-waiter.log"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

remain_s() {
  local stop now
  stop="$(date -u -d "$STOP_AT" +%s)"
  now="$(date -u +%s)"
  echo $((stop - now))
}

run_probe() {
  local id="$1" n="$2" side="$3" grids="$4" seed="$5" windows="$6" deadline="$7"
  local prefix="$ROOT/${id}"
  if [[ -f "${prefix}-run.json" ]]; then
    echo "$(ts) SKIP ${id}: run JSON exists" | tee -a "$LOG"
    return 0
  fi
  local remain
  remain="$(remain_s)"
  if (( remain < 60 )); then
    echo "$(ts) STOP before ${id}: remain=${remain}s" | tee -a "$LOG"
    return 2
  fi
  echo "$(ts) START ${id} deadline=${deadline}s remain=${remain}s" | tee -a "$LOG"
  (
    cd "$PACKING"
    export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
    uv run --frozen --all-extras --group dev python -m devtools.run_fractional_colgen \
      --n "$n" --side "$side" --shrink 9977/10000 --direction-steps 181 \
      --grid-counts "$grids" --scale 4000000 --support-cap 32 \
      --column-rounds 1 --max-rounds 60 --deadline-seconds "$deadline" \
      --seed-certificate "$seed" --seed-map scale \
      --seed-windows "$windows" \
      --freeze "${prefix}-certificate.json" \
      --freeze-family "${prefix}-family.json" \
      --json "${prefix}-run.json" \
      --row-log "${prefix}-rows.jsonl" \
      --log "${prefix}.log"
  )
  local rc=$?
  echo "$(ts) EXIT ${id} rc=${rc}" | tee -a "$LOG"
  if [[ -f "${prefix}-certificate.json" && -f "${prefix}-run.json" ]]; then
    local below
    below="$(
      cd "$PACKING" && uv run --frozen python - "$n" "${prefix}-run.json" <<'PY'
from __future__ import annotations

import json
import sys
from fractions import Fraction

n = int(sys.argv[1])
payload = json.loads(open(sys.argv[2]).read())
mass = payload.get("total_mass")
if mass is None:
    raise SystemExit(2)
print("yes" if Fraction(mass) < n else "no")
PY
    )"
    if [[ "$below" == "yes" ]]; then
      echo "$(ts) ${id}: freeze mass < ${n}; coordinator must decide_certificate" | tee -a "$LOG"
      return 3
    fi
    echo "$(ts) ${id}: freeze mass >= ${n}; site set refuted, continue" | tee -a "$LOG"
    return 0
  fi
  echo "$(ts) ${id}: no freeze (unconverged or mass not rationalised)" | tee -a "$LOG"
  return 0
}

echo "$(ts) waiter start; stop_at=${STOP_AT}" | tee -a "$LOG"

# n=20 may already be running in tmux lb-n20-973-200. Wait for its JSON
# or the session, then continue the remaining ranks.
N20="$ROOT/n20-973-200-t021-grid4-windows7-run.json"
if [[ ! -f "$N20" ]]; then
  echo "$(ts) waiting for in-flight n=20 run JSON" | tee -a "$LOG"
  while [[ ! -f "$N20" ]]; do
    remain="$(remain_s)"
    if (( remain < 60 )); then
      echo "$(ts) STOP waiting for n=20: remain=${remain}s" | tee -a "$LOG"
      exit 2
    fi
    sleep 30
  done
  echo "$(ts) n=20 run JSON present" | tee -a "$LOG"
fi

run_probe n12-397-100-t017-grid4-windows7 12 397/100 28,38,46,54 \
  cases/n12_fractional_certificate/certificate.json 7 1200 || {
  rc=$?
  if (( rc != 0 )); then exit "$rc"; fi
}
run_probe n17-23-5-t019-grid4-windows8 17 23/5 34,45,56,64 \
  cases/n17_fractional_certificate/certificate.json 8 1200 || {
  rc=$?
  if (( rc != 0 )); then exit "$rc"; fi
}
run_probe n19-481-100-t020-auto-windows6 19 481/100 34,45,56 \
  cases/n20_fractional_certificate/certificate-24-5.json 6 1200 || {
  rc=$?
  if (( rc != 0 )); then exit "$rc"; fi
}
run_probe n18-4675-1000-t027-auto-windows5 18 4675/1000 auto \
  cases/n18_fractional_certificate/certificate.json 5 1200 || {
  rc=$?
  if (( rc != 0 )); then exit "$rc"; fi
}

echo "$(ts) waiter done" | tee -a "$LOG"
