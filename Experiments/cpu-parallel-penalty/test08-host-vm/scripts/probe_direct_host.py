"""Record whether the VM can execute a read-only command on its PVE gateway."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
           "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no",
           "root@192.168.100.1", "/bin/true"]
result = subprocess.run(command, capture_output=True, text=True, timeout=6)
record = {"utc": datetime.now(timezone.utc).isoformat(),
          "target": "PVE gateway 192.168.100.1",
          "command": command, "exit_code": result.returncode,
          "stdout": result.stdout, "stderr": result.stderr,
          "direct_host_execution_available": result.returncode == 0}
raw = HERE.parent / "raw"
raw.mkdir(exist_ok=True)
(raw / "direct-host-access.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
