#!/usr/bin/env bash
out=/root/cpu-parallel-penalty-host/phase-a-pinning
while test ! -e "$out/RESTORED"; do
  if test -e "$out/RESTORE"; then
    bash "$out/restore.sh" && exit 0
  fi
  sleep 1
done
