"""Per-batch cost, turns and tool use; per-question per-entity `changes` calls (the "dig")."""
import json, sys
from collections import Counter
from pathlib import Path

QS = ["S01", "S02", "S03", "S04", "S05", "S06a", "S06b", "S06c", "S07", "S08"]
for d in sys.argv[1:]:
    cost = turns = 0.0; tools = Counter(); dig = {}
    for q in QS:
        n = 0
        for line in (Path(d) / f"{q}.jsonl").read_text().splitlines():
            e = json.loads(line)
            if e.get("type") == "result":
                cost += e.get("total_cost_usd") or 0; turns += e.get("num_turns") or 0
            if e.get("type") == "assistant":
                for c in e["message"].get("content", []):
                    if c.get("type") == "tool_use":
                        name = c["name"].replace("mcp__utopia__", ""); tools[name] += 1
                        if name == "changes" and any(k in c.get("input", {}) for k in ("entity", "entity_id", "name")):
                            n += 1
        dig[q] = n
    print(f"{d}: ${cost:.2f}, {int(turns)} turns; tools {dict(tools.most_common())}")
    print("   per-entity changes:", " ".join(f"{q}={dig[q]}" for q in QS))
