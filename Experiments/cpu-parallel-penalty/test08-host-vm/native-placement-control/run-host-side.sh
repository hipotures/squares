#!/usr/bin/env bash
set -euo pipefail

shared_dir=${1:?usage: run-host-side.sh HOST_SHARED_TEST08_DIR}
out=/root/cpu-parallel-penalty-host/native-placement-control

test -f "$shared_dir/tail-retest-package.tar.gz"
test ! -e "$shared_dir/NATIVE_PINNED"
test ! -e "$shared_dir/NATIVE_RESTORE"
test ! -e "$shared_dir/NATIVE_RESTORED"

bash "$shared_dir/native8-pin.sh" "$shared_dir"
test -e "$shared_dir/NATIVE_PINNED"
echo 'PINNED: VM may start the 8/16-worker control. Waiting for its restore marker.'

for _ in $(seq 1 500); do
  test -e "$out/RESTORED" && break
  sleep 1
done
if test ! -e "$out/RESTORED"; then
  echo 'Restore marker did not appear before deadline; restoring now.'
  bash "$out/restore.sh"
fi
test -e "$out/RESTORED"

mkdir -p "$shared_dir/native-placement-host"
cp -a "$out/." "$shared_dir/native-placement-host/"
chmod -R a+rX "$shared_dir/native-placement-host"
date -Is > "$shared_dir/NATIVE_RESTORED"
chmod 644 "$shared_dir/NATIVE_RESTORED"
echo 'RESTORED: original affinity verified for all 16 vCPU threads; logs copied.'
