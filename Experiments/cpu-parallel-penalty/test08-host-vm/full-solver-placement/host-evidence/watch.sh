#!/usr/bin/env bash
out=/root/cpu-parallel-penalty-host/full-solver8-placement
while test ! -e "$out/RESTORED"; do
  shared_marker=$(cat "$out/shared-restore-marker-path")
  if test -e "$out/RESTORE" || test -e "$shared_marker"; then
    bash "$out/restore.sh" && exit 0
  fi
  sleep 1
done
