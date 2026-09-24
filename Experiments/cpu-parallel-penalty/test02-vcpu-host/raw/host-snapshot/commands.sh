#!/usr/bin/env bash
set -u
out=/root/cpu-parallel-penalty-host/phase-a
vmid=207
mkdir -p "$out"
date -Is > "$out/collected-at.txt"
hostname -f > "$out/hostname.txt"
qm status "$vmid" > "$out/qm-status.txt" 2>&1
qm config "$vmid" > "$out/qm-config.txt" 2>&1
pid=$(cat "/run/qemu-server/${vmid}.pid")
if ! test -r "/proc/$pid/cmdline" || ! tr '\0' ' ' < "/proc/$pid/cmdline" | grep -q -- "-id $vmid"; then
  printf 'QEMU PID validation failed: VMID=%s PID=%s\n' "$vmid" "$pid" >&2
  exit 1
fi
printf 'VMID=%s\nQEMU_PID=%s\n' "$vmid" "$pid" > "$out/identifiers.txt"
ps -p "$pid" -o pid,ppid,user,comm,args > "$out/qemu-process.txt"
tr '\0' ' ' < "/proc/$pid/cmdline" > "$out/qemu-cmdline.txt"
printf '\n' >> "$out/qemu-cmdline.txt"
lscpu -e > "$out/lscpu-e.txt"
lscpu -J > "$out/lscpu-J.json"
lscpu -e=CPU,NODE,SOCKET,CORE,ONLINE > "$out/topology-cpu-node-socket-core.txt"
for node in /sys/devices/system/node/node[0-9]*; do
  test -d "$node" || continue
  printf '%s cpulist=' "$(basename "$node")"
  cat "$node/cpulist"
done > "$out/numa-nodes.txt"
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
  test -d "$cpu/topology" || continue
  printf '%s package=' "$(basename "$cpu")"
  cat "$cpu/topology/physical_package_id" | tr '\n' ' '
  printf 'core='
  cat "$cpu/topology/core_id" | tr '\n' ' '
  printf 'smt_siblings='
  cat "$cpu/topology/thread_siblings_list"
done > "$out/topology-smt.txt"
ps -T -p "$pid" -o pid,tid,psr,comm > "$out/qemu-all-threads.txt"
: > "$out/vcpu-threads.txt"
: > "$out/vcpu-affinity.txt"
for commfile in /proc/"$pid"/task/[0-9]*/comm; do
  tid=${commfile%/comm}; tid=${tid##*/}
  name=$(cat "$commfile")
  if [[ "$name" =~ ^CPU[[:space:]][0-9]+(/KVM)?$ ]]; then
    printf 'TID=%s COMM=%s\n' "$tid" "$name" >> "$out/vcpu-threads.txt"
    printf 'TID=%s COMM=%s\n' "$tid" "$name" >> "$out/vcpu-affinity.txt"
    taskset -pc "$tid" >> "$out/vcpu-affinity.txt" 2>&1
    ps -p "$tid" -o tid,psr,comm >> "$out/vcpu-affinity.txt" 2>&1
    grep '^Cpus_allowed_list:' "/proc/$pid/task/$tid/status" >> "$out/vcpu-affinity.txt" 2>&1
  fi
done
cat "/proc/$pid/cgroup" > "$out/qemu-cgroup.txt"
findmnt -T /sys/fs/cgroup > "$out/cgroup-mount.txt"
cg=$(awk -F: '$1=="0" {print $3}' "/proc/$pid/cgroup")
if [[ -n "$cg" ]]; then
  : > "$out/cgroup-cpu.txt"
  while :; do
    dir="/sys/fs/cgroup$cg"
    printf '\nCGROUP=%s\n' "$cg" >> "$out/cgroup-cpu.txt"
    for file in cpu.max cpu.stat; do
      printf '%s:\n' "$file" >> "$out/cgroup-cpu.txt"
      if test -r "$dir/$file"; then cat "$dir/$file" >> "$out/cgroup-cpu.txt"; else printf 'unavailable\n' >> "$out/cgroup-cpu.txt"; fi
    done
    test "$cg" = / && break
    cg=${cg%/*}
    test -n "$cg" || cg=/
  done
else
  printf 'No unified cgroup v2 entry found\n' > "$out/cgroup-cpu.txt"
fi
{
  printf 'perf_path='; command -v perf || true
  printf 'perf_version='; perf --version 2>&1 || true
  for f in /proc/sys/kernel/perf_event_paranoid /proc/sys/kernel/nmi_watchdog /proc/sys/kernel/kptr_restrict; do
    printf '%s=' "$f"; cat "$f" 2>&1 || true
  done
  printf '\nPMU device names:\n'
  for dev in /sys/bus/event_source/devices/*; do test -d "$dev" && basename "$dev"; done
  printf '\nUMC/DF PMU details:\n'
  for dev in /sys/bus/event_source/devices/*; do
    test -d "$dev" || continue
    name=$(basename "$dev")
    case "$name" in *umc*|*UMC*|*df*|*DF*)
      printf '\n%s\n' "$name"
      for f in type cpumask format/* events/* caps/*; do
        for path in "$dev"/$f; do
          test -f "$path" || continue
          printf '%s=' "${path#"$dev"/}"
          cat "$path" 2>&1 || true
        done
      done
    ;; esac
  done
} > "$out/perf-pmu-availability.txt"
if command -v perf >/dev/null 2>&1; then
  perf list --no-desc > "$out/perf-list.txt" 2>&1 || true
  rg -i '(^|[^a-z])(umc|df|data.fabric)([^a-z]|$)' "$out/perf-list.txt" > "$out/perf-umc-df-matches.txt" 2>/dev/null || grep -iE 'umc|data.fabric|(^|[^a-z])df([^a-z]|$)' "$out/perf-list.txt" > "$out/perf-umc-df-matches.txt" || true
fi
printf 'VMID=%s PID=%s vCPU_threads=%s\n' "$vmid" "$pid" "$(wc -l < "$out/vcpu-threads.txt")"
ls -l "$out"
