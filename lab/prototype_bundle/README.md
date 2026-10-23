# The port bundle (lab plan L1)

What the prototype's builder reads of the lab, and nothing else (spec §11.3, §11.4).

| File | What it does |
|---|---|
| `allowlist.yaml` | Names every file that may leave, per source repo and pinned commit |
| `scrub.yaml` | Rewrites lines that cite scenarios, traps or truth as the mechanisms they protect (L1.2) |
| `scan.py` | The private scan: truth-derived terms built at run time, reported by kind only (L1.3) |
| `export.py` | Reads from git, applies the scrub, scans, writes the bundle and `FILES.sha256` (L1.1) |

```bash
PYTHONPATH=lab uv run python -m prototype_bundle.export --commit <sha> \
  --out ../prototype-bundle/<date>-<short sha>/      # LW-3; refuses to overwrite
PYTHONPATH=lab uv run python -m prototype_bundle.scan <path> ...   # counts by kind, never terms
```

The deny list in `export.py` wins over the allowlist for the lab repo. Any scan hit means nothing is
written. This package, its tests and the lab's plan are never exported themselves.
