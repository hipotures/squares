#!/usr/bin/env bash
set -u
out=/root/cpu-parallel-penalty-host/full-solver8-placement
exec 9>"$out/restore.lock"
flock -x 9
start() { sed 's/^.*) //' "$1" | awk '{print $20}'; }
read -r pid original_start < "$out/qemu-identity.txt"
{
  printf 'RESTORE_STARTED %s\n' "$(date -Is)"
  if test ! -r "/proc/$pid/stat" || test "$(start "/proc/$pid/stat")" != "$original_start"; then
    echo 'QEMU process no longer matches; old TIDs will not be touched'
    exit 1
  fi
  failed=0
  while IFS=$'\t' read -r i tid aff thread_start; do
    if test ! -r "/proc/$pid/task/$tid/stat" || test "$(start "/proc/$pid/task/$tid/stat")" != "$thread_start" || test "$(cat "/proc/$pid/task/$tid/comm")" != "CPU $i/KVM"; then
      echo "CPU $i TID $tid no longer matches; skipped"
      failed=1
      continue
    fi
    taskset -pc "$aff" "$tid" || failed=1
    line=$(taskset -pc "$tid")
    echo "$line"
    test "${line##*: }" = "$aff" || failed=1
  done < "$out/before.tsv"
  if test "$failed" -eq 0; then
    date -Is > "$out/RESTORED"
    printf 'RESTORED_OK %s\n' "$(date -Is)"
  else
    printf 'RESTORE_INCOMPLETE %s\n' "$(date -Is)"
  fi
  exit "$failed"
} >> "$out/log.txt" 2>&1
