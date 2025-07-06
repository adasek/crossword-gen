import json
import sys

with open("mypy-report.json") as f:
    errors = json.load(f)

for error in errors:
    file = error["file"]
    line = error["line"]
    col = error.get("column", 1)
    msg = error["message"]
    print(f"::error file={file},line={line},col={col}::{msg}")

if len(errors) > 0:
    print(f"Found {len(errors)} mypy issues")
    sys.exit(1)
else:
    sys.exit(0)
