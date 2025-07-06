import json
import sys

with open("pylint-report.json") as f:
    errors = json.load(f)

levels = {"error": "error", "warning": "warning", "refactor": "warning", "convention": "notice"}

for error in errors:
    path = error.get("path")
    line = error.get("line")
    col = error.get("column")
    msg_id = error.get("symbol")
    message = error.get("message")
    level = levels.get(error.get("type"), "warning")

    print(f"::{level} file={path},line={line},col={col}::{msg_id}: {message}")

if len(errors) > 0:
    print(f"Found {len(errors)} pylint issues")
    sys.exit(1)
else:
    sys.exit(0)
