import json
import sys

with open("pylint-report.json") as f:
    data = json.load(f)

levels = {"error": "error", "warning": "warning", "refactor": "warning", "convention": "notice"}

for msg in data:
    path = msg.get("path")
    line = msg.get("line")
    col = msg.get("column")
    msg_id = msg.get("symbol")
    message = msg.get("message")
    level = levels.get(msg.get("type"), "warning")

    print(f"::{level} file={path},line={line},col={col}::{msg_id}: {message}")

if len(errors) > 0:
    sys.exit(1)
else:
    sys.exit(0)
