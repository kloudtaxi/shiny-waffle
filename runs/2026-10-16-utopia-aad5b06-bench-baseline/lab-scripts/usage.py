"""Sum the bench server's `llm usage` log lines. Usage: python3 -I usage.py LOG [SINCE_ISO] [UNTIL_ISO]"""
import re, sys, json
from collections import defaultdict
log, since, until = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else ""), (sys.argv[3] if len(sys.argv) > 3 else "~")
ansi = re.compile(r"\x1b\[[0-9;]*m")
tot = defaultdict(lambda: {"calls": 0, "prompt": 0, "completion": 0, "cached": 0})
for line in open(log, encoding="utf-8", errors="replace"):
    line = ansi.sub("", line)
    if "llm usage" not in line:
        continue
    ts = line[:27]
    if not (since <= ts < until):
        continue
    f = dict(re.findall(r"(\w+)=(\S+)", line))
    t = tot[f.get("model", "?").strip("\"")]
    t["calls"] += 1
    for k in ("prompt", "completion", "cached"):
        v = re.sub(r"\D", "", f.get(k, "") or "")
        t[k] += int(v) if v else 0
print(json.dumps(tot, indent=1))
