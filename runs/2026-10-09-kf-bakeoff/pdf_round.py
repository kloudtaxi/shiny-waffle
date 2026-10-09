"""The PDF round (`addendum-pdf.md`): render the documents to PDF, parse them back with Docling,
measure what survives, then extract from Docling's text with the bake-off's pipelines.

    KF=<scratchpad>/kfenv/bin/python
    $KF runs/2026-10-09-kf-bakeoff/pdf_round.py render <workdir>   # pandoc + headless Chrome
    $KF runs/2026-10-09-kf-bakeoff/pdf_round.py parse <workdir>    # Docling + fidelity
    $KF runs/2026-10-09-kf-bakeoff/pdf_round.py render <workdir>   # pandoc + Chrome
    $KF runs/2026-10-09-kf-bakeoff/pdf_round.py score <workdir>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bakeoff  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = (
    "body{font-family:Helvetica,Arial,sans-serif;font-size:11pt;margin:2cm}"
    "table{border-collapse:collapse}td,th{border:1px solid #444;padding:4px}"
)


def render(work: Path) -> None:
    (work / "md").mkdir(parents=True, exist_ok=True)
    (work / "pdf").mkdir(exist_ok=True)
    (work / "style.css").write_text(CSS)
    for name, text in bakeoff.docs().items():
        md = work / "md" / name
        md.write_text(text)
        html = md.with_suffix(".html")
        subprocess.run(
            [
                "pandoc",
                str(md),
                "-s",
                "-o",
                str(html),
                "--css",
                str(work / "style.css"),
                "--metadata",
                "title= ",
            ],
            check=True,
            capture_output=True,
        )
        pdf = work / "pdf" / (Path(name).stem + ".pdf")
        subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}",
                f"file://{html}",
            ],
            capture_output=True,
        )
    print(f"rendered {len(list((work / 'pdf').glob('*.pdf')))} PDFs")


def parse(work: Path) -> None:
    from docling.document_converter import DocumentConverter

    conv = DocumentConverter()
    (work / "docling").mkdir(exist_ok=True)
    for pdf in sorted((work / "pdf").glob("*.pdf")):
        md = conv.convert(str(pdf)).document.export_to_markdown()
        (work / "docling" / (pdf.stem + ".md")).write_text(md)
    fidelity(work)


def table_rows(text: str) -> list[str]:
    return [
        ln
        for ln in text.splitlines()
        if ln.strip().startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", ln.strip())
    ]


def fidelity(work: Path) -> None:
    gold = bakeoff.gold()
    src = bakeoff.docs()
    out: dict[str, Any] = {"surfaces": {}, "tables": {}, "nesting": {}}
    kept = total = 0
    for doc, facts in gold.items():
        dtext = (work / "docling" / (Path(doc).stem + ".md")).read_text()
        flat = " ".join(dtext.split())
        k = sum(" ".join(f["surface"].split()) in flat for f in facts)
        out["surfaces"][doc] = [k, len(facts)]
        kept, total = kept + k, total + len(facts)
    out["surfaces_kept"] = round(kept / total, 3)
    rows_src = rows_kept = 0
    for name, text in src.items():
        srows = table_rows(text)
        if len(srows) < 2:
            continue
        dtext = (work / "docling" / (Path(name).stem + ".md")).read_text()
        drows = table_rows(dtext)
        n_data = len(srows) - 1  # minus the header row
        got = max(0, min(n_data, len(drows) - 1))
        out["tables"][name] = [got, n_data]
        rows_src, rows_kept = rows_src + n_data, rows_kept + got
    out["table_rows_kept"] = round(rows_kept / max(rows_src, 1), 3)
    ind_src = ind_kept = 0
    for chart in ("organization_chart.md", "support_org_chart.md"):
        s = [ln for ln in src[chart].splitlines() if re.match(r"^\s{2,}[-*]\s", ln)]
        dtext = (work / "docling" / (Path(chart).stem + ".md")).read_text()
        d = [ln for ln in dtext.splitlines() if re.match(r"^\s{2,}[-*]\s", ln)]
        out["nesting"][chart] = [len(d), len(s)]
        ind_src, ind_kept = ind_src + len(s), ind_kept + min(len(d), len(s))
    out["nested_items_kept"] = round(ind_kept / max(ind_src, 1), 3)
    (HERE / "pdf-fidelity.json").write_text(json.dumps(out, indent=1) + "\n")
    print({k: v for k, v in out.items() if not isinstance(v, dict)})


def docling_docs(work: Path) -> dict[str, str]:
    return {
        name: (work / "docling" / (Path(name).stem + ".md")).read_text() for name in bakeoff.docs()
    }


def extract(work: Path) -> None:
    texts = docling_docs(work)
    for p in ("baseline", "langextract"):
        fn = bakeoff.PIPELINES[p]
        res = {}
        for n, t in texts.items():
            try:
                res[n] = fn(f"pdf:{n}", t)
            except Exception as e:  # noqa: BLE001
                res[n] = {"error": f"{type(e).__name__}: {e}"[:300]}
        (bakeoff.OUT / f"pdf-{p}.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
        print(p, sum(len(v) for v in res.values() if isinstance(v, list)), "facts")


def score(work: Path) -> None:
    """The bake-off's scoring, with Docling's text as the document text for grounding."""
    gold = bakeoff.gold()  # gold from the source text, matched by value
    texts = docling_docs(work)
    report: dict[str, Any] = {}
    for p in ("baseline", "langextract"):
        res = json.loads((bakeoff.OUT / f"pdf-{p}.json").read_text())
        tp: dict[str, int] = {}
        n_in = loc = 0
        for doc, facts in res.items():
            facts = facts if isinstance(facts, list) else []
            want = list(gold.get(doc, []))
            used = [False] * len(want)
            for x in facts:
                if x.get("predicate") not in bakeoff.PREDICATES or doc not in gold:
                    continue
                n_in += 1
                loc += bakeoff.grounded(x, texts[doc])["locatable"]
                hit = next(
                    (i for i, gf in enumerate(want) if not used[i] and bakeoff.matches(gf, x)), None
                )
                if hit is not None:
                    used[hit] = True
                    tp[x["predicate"]] = tp.get(x["predicate"], 0) + 1
        n_gold = sum(len(v) for v in gold.values())
        report[p] = {
            "recall": round(sum(tp.values()) / n_gold, 3),
            "tp": tp,
            "precision_on_gold_docs": round(sum(tp.values()) / max(n_in, 1), 3),
            "locatable": round(loc / max(n_in, 1), 3),
        }
        print(p, report[p])
    report["usd_pdf_extraction"] = round(
        sum(r["usd"] for r in bakeoff.claude_cli._load().values() if ":pdf:" in str(r.get("tag"))),
        2,
    )
    (HERE / "pdf-results.json").write_text(json.dumps(report, indent=1) + "\n")


def main() -> None:
    step, work = sys.argv[1], Path(sys.argv[2])
    {"render": render, "parse": parse, "extract": extract, "score": score}[step](work)


if __name__ == "__main__":
    main()
