"""Demonstrate automatic basis retention when highspy appends rows."""
import json
from pathlib import Path

import highspy
import numpy as np


def main():
    model = highspy.Highs()
    model.setOptionValue("output_flag", False)
    model.addCols(2, np.array([1.0, 1.0]), np.zeros(2),
                  np.full(2, highspy.kHighsInf), 0,
                  np.zeros(3, dtype=np.int32), np.empty(0, dtype=np.int32),
                  np.empty(0))
    records = []
    for index in range(3):
        before = model.getBasis()
        model.addRows(1, np.array([-highspy.kHighsInf]), np.array([-1.0]),
                      2, np.array([0, 2], dtype=np.int32),
                      np.array([0, 1], dtype=np.int32), np.array([-1.0, -1.0]))
        after_append = model.getBasis()
        model.run()
        solved = model.getBasis()
        records.append({
            "index": index,
            "valid_before_append": bool(before.valid),
            "valid_after_append": bool(after_append.valid),
            "valid_after_solve": bool(solved.valid),
            "row_status_count_after_append": len(after_append.row_status),
            "objective": model.getObjectiveValue(),
        })
    result = {"highspy_version": model.version(), "records": records}
    Path(__file__).with_name("basis_probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
