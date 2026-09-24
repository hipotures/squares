#!/usr/bin/env bash
set -u
out=/root/cpu-parallel-penalty-host/phase-a
{
  date -Is
  printf 'perf_path='; command -v perf || true
  printf 'perf_version='; perf --version 2>&1 || true
  printf 'perf_event_paranoid='; cat /proc/sys/kernel/perf_event_paranoid
  printf '\nPMU devices:\n'
  for dev in /sys/bus/event_source/devices/*; do test -d "$dev" && basename "$dev"; done
  printf '\nUMC/DF PMU details:\n'
  for dev in /sys/bus/event_source/devices/*; do
    test -d "$dev" || continue
    name=$(basename "$dev")
    case "$name" in *umc*|*UMC*|*df*|*DF*)
      printf '\n%s\n' "$name"
      for pattern in type cpumask format/* events/* caps/*; do
        for path in "$dev"/$pattern; do
          test -f "$path" || continue
          printf '%s=' "${path#"$dev"/}"
          cat "$path" 2>&1 || true
        done
      done
    ;; esac
  done
} > "$out/perf-availability-after-install.txt"
perf list --no-desc > "$out/perf-list-after-install.txt" 2>&1
printf 'perf_list_exit_code=%s\n' "$?" >> "$out/perf-availability-after-install.txt"
grep -iE 'umc|data.fabric|(^|[^a-z])df([^a-z]|$)' "$out/perf-list-after-install.txt" > "$out/perf-umc-df-after-install.txt" || true
printf 'perf_version=%s\n' "$(perf --version)"
printf 'pmu_count=%s\n' "$(find /sys/bus/event_source/devices -mindepth 1 -maxdepth 1 -type l | wc -l)"
printf 'umc_df_matches=%s\n' "$(wc -l < "$out/perf-umc-df-after-install.txt")"
printf 'PERF-CHECK-DONE\n'
