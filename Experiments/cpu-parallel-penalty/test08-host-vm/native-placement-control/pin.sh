#!/usr/bin/env bash
set -euo pipefail
umask 077
out=/root/cpu-parallel-penalty-host/native-placement-control
shared_dir=${1:?usage: pin.sh HOST_SHARED_TEST08_DIR}
test -d "$shared_dir"
test -f "$shared_dir/tail-retest-package.tar.gz"
test ! -e "$shared_dir/NATIVE_RESTORE"
mkdir -p "$out"
printf '%s\n' "$shared_dir/NATIVE_RESTORE" > "$out/shared-restore-marker-path"
exec > >(tee -a "$out/log.txt") 2>&1
printf 'START %s\n' "$(date -Is)"
pid=$(cat /run/qemu-server/207.pid)
tr '\0' ' ' < "/proc/$pid/cmdline" | grep -q -- '-id 207'
start() { sed 's/^.*) //' "$1" | awk '{print $20}'; }
printf '%s %s\n' "$pid" "$(start "/proc/$pid/stat")" > "$out/qemu-identity.txt"
: > "$out/before.tsv"
: > "$out/before-taskset.txt"
for i in $(seq 0 15); do
  siblings=$(cat "/sys/devices/system/cpu/cpu$i/topology/thread_siblings_list")
  test "$siblings" = "$i,$((i+16))" || { echo "Unexpected SMT topology for CPU $i: $siblings"; exit 1; }
  tid=''
  for f in /proc/"$pid"/task/*/comm; do
    test "$(cat "$f")" = "CPU $i/KVM" && { tid=${f%/comm}; tid=${tid##*/}; break; }
  done
  test -n "$tid" || { echo "Missing CPU $i/KVM"; exit 1; }
  line=$(taskset -pc "$tid")
  printf '%s\n' "$line" >> "$out/before-taskset.txt"
  aff=${line##*: }
  [[ "$aff" =~ ^[0-9,-]+$ ]] || exit 1
  printf '%s\t%s\t%s\t%s\n' "$i" "$tid" "$aff" "$(start "/proc/$pid/task/$tid/stat")" >> "$out/before.tsv"
done
test "$(wc -l < "$out/before.tsv")" -eq 16
cat > "$out/restore.sh" <<'RESTORE'
#!/usr/bin/env bash
set -u
out=/root/cpu-parallel-penalty-host/native-placement-control
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
RESTORE
cat > "$out/watch.sh" <<'WATCH'
#!/usr/bin/env bash
out=/root/cpu-parallel-penalty-host/native-placement-control
while test ! -e "$out/RESTORED"; do
  shared_marker=$(cat "$out/shared-restore-marker-path")
  if test -e "$out/RESTORE" || test -e "$shared_marker"; then
    bash "$out/restore.sh" && exit 0
  fi
  sleep 1
done
WATCH
chmod 700 "$out/restore.sh" "$out/watch.sh"
systemd-run --unit=cpu207-native8-restore-auto --on-active=8min --timer-property=AccuracySec=1s /bin/bash "$out/restore.sh"
systemd-run --unit=cpu207-native8-restore-watch /bin/bash "$out/watch.sh"
systemctl is-active --quiet cpu207-native8-restore-auto.timer
systemctl is-active --quiet cpu207-native8-restore-watch.service
printf 'GUARDS_ACTIVE %s\n' "$(date -Is)"
test ! -e "$out/RESTORE" && test ! -e "$out/RESTORED"
: > "$out/after-taskset.txt"
while IFS=$'\t' read -r i tid aff thread_start; do
  taskset -pc "$i" "$tid"
done < "$out/before.tsv"
failed=0
while IFS=$'\t' read -r i tid aff thread_start; do
  line=$(taskset -pc "$tid")
  echo "$line" | tee -a "$out/after-taskset.txt"
  test "${line##*: }" = "$i" || failed=1
done < "$out/before.tsv"
if test "$failed" -ne 0 || test "$(wc -l < "$out/after-taskset.txt")" -ne 16; then
  echo 'PIN_VERIFICATION_FAILED; restoring'
  bash "$out/restore.sh"
  exit 1
fi
date -Is > "$out/PINNED"
printf 'PINNED %s verified=16/16 auto_restore=8min\n' "$(cat "$out/PINNED")"
printf '%s\n' "$(cat "$out/PINNED")" > "$shared_dir/NATIVE_PINNED"
chmod 644 "$shared_dir/NATIVE_PINNED"
