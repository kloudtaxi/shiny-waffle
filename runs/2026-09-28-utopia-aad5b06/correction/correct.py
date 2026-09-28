"""Correction run: identity-only review corrections, as a reviewer with source-system access.

APPLIED 2026-09-28 17:25:39-41 UTC to both Northstar KBs; `actions.jsonl` is the log. This file
is kept as the record of exactly what was done. Re-running it is a no-op at best: the agent
decisions it answers are settled and its merge sources are gone. So it prints the plan
unless given `--apply`.

Order: (1) answer open agent proposals, (2) overturn wrong automatic keeps, (3) manual merges
for pairs never compared, resolved by name at execution time, because earlier merges retire
entity ids. Every action carries a rationale citing the source row; every response is logged.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(LAB / "lab" / "utopia"))
import utopia as ut  # noqa: E402

RUN = Path(__file__).resolve().parent
KB = "01a0e787-41f4-71b2-83fb-22aefb8dd650"
KB5 = "01a0e787-457c-7f50-a8f1-e33beb27dfb3"
DB_CONTAINER = os.environ.get("UTOPIA_DB_CONTAINER", "utopia-db-1")

SKU = "products.csv lists these as different SKUs/products"
PLAN = [
    # ---- base: open proposals ----------------------------------------------------------
    (
        KB,
        "answer",
        "01a0e78a-ee24-7742-86b4-53e8205c609e",
        "merge",
        "Same SKU NS-830-EQU (products.csv).",
    ),
    (
        KB,
        "answer",
        "01a0e78a-ee2d-7362-ba74-b5e349f7d939",
        "keep",
        SKU + ": NS-830-EQU vs PROD-001 NS-500.",
    ),
    (KB, "answer", "01a0e78a-ee36-73e1-bac1-ee75564082c5", "keep", SKU + "."),
    (KB, "answer", "01a0e78a-ee4d-7d02-b990-45946c7d1a58", "keep", SKU + "."),
    (KB, "answer", "01a0e78a-ee58-70a1-999a-dd523283238d", "keep", SKU + "."),
    # ---- base: overturn wrong automatic keeps ------------------------------------------
    (
        KB,
        "answer",
        "01a0e78a-ca4e-77c1-bcf2-1ec1b6924208",
        "merge",
        "products.csv: PROD-002 has sku NS-CLOUD and name NS-Cloud Operations Suite — one product.",
    ),
    (
        KB,
        "answer",
        "01a0e788-dd84-7fb0-b956-2bd41fb1cdaf",
        "merge",
        "Service ticket SR-40418 names 'Acme Industrial (CRM-2091)'; crm_accounts.csv CRM-2091 is "
        "Acme Industrial Supply Co. — one customer.",
    ),
    # ---- base: manual merges (never compared) ------------------------------------------
    (
        KB,
        "merge",
        ("NS-500 Industrial Controller", "NS-500 Industrial Controller"),
        None,
        "Two entities with the same product name; products.csv has one PROD-001.",
    ),
    (
        KB,
        "merge",
        ("C-1001", "Acme Mfg. Holdings"),
        None,
        "customers.csv: erp_customer_id C-1001 is Acme Mfg. Holdings.",
    ),
    (
        KB,
        "merge",
        ("C-1044", "Acme Industrial Supply Co."),
        None,
        "customers.csv: erp_customer_id C-1044 is Acme Industrial Supply Co.",
    ),
    (
        KB,
        "merge",
        ("sarah.chen@northstar.example", "Sarah Chen"),
        None,
        "employees.csv: EMP-101 Sarah Chen, email sarah.chen@northstar.example.",
    ),
    (
        KB,
        "merge",
        ("michael.torres@northstar.example", "Michael Torres"),
        None,
        "employees.csv: EMP-200 Michael Torres, email michael.torres@northstar.example.",
    ),
    # ---- variant: open proposals -------------------------------------------------------
    (
        KB5,
        "answer",
        "01a0e788-107f-7db0-8646-453e04328e59",
        "merge",
        "employees.csv has one Michael Torres (EMP-200, VP Sales).",
    ),
    (
        KB5,
        "answer",
        "01a0e789-45d0-76b2-b6db-5c4b378e4142",
        "keep",
        SKU + ": NS-840-SER vs PROD-001 NS-500.",
    ),
    (KB5, "answer", "01a0e789-45dc-7861-be59-9e394e78731a", "keep", SKU + "."),
    (KB5, "answer", "01a0e789-45e9-7241-b64c-3eec62bf69d9", "keep", SKU + "."),
    # ---- variant: overturn wrong automatic keeps ---------------------------------------
    (
        KB5,
        "answer",
        "01a0e788-d68f-7e61-b898-ad0bfef34ce6",
        "merge",
        "crm_accounts.csv CRM-2048 'Acme Manufacturing' and customers.csv C-1001 'Acme Mfg. "
        "Holdings' "
        "share DUNS 04-812-7730 and 2200 N Industrial Pkwy, Milwaukee — one customer.",
    ),
    (
        KB5,
        "answer",
        "01a0e788-bfd5-7cf0-b301-586be56bc23b",
        "merge",
        "products.csv: PROD-001 NS-500 Industrial Controller, sku NS-500 — 'NS-500 controller' is "
        "it.",
    ),
    (
        KB5,
        "answer",
        "01a0e78a-c9f9-7010-a890-c71c4997560d",
        "merge",
        "products.csv: PROD-002 has sku NS-CLOUD and name NS-Cloud Operations Suite — one product.",
    ),
    (
        KB5,
        "answer",
        "01a0e788-dca3-7522-902c-9a3547df41ba",
        "merge",
        "Service ticket SR-40418 names 'Acme Industrial (CRM-2091)'; crm_accounts.csv CRM-2091 is "
        "Acme Industrial Supply Co. — one customer.",
    ),
    # ---- variant: manual merges --------------------------------------------------------
    (
        KB5,
        "merge",
        ("C-1001", "ACME Manufacturing|Acme Mfg. Holdings"),
        None,
        "customers.csv: erp_customer_id C-1001 is Acme Mfg. Holdings (= CRM-2048 Acme "
        "Manufacturing).",
    ),
    (
        KB5,
        "merge",
        ("CRM-2048", "ACME Manufacturing|Acme Mfg. Holdings"),
        None,
        "crm_accounts.csv: account_id CRM-2048 is Acme Manufacturing.",
    ),
    (
        KB5,
        "merge",
        ("C-1044", "Acme Industrial Supply Co."),
        None,
        "customers.csv: erp_customer_id C-1044 is Acme Industrial Supply Co.",
    ),
    (
        KB5,
        "merge",
        ("michael.torres@northstar.example", "Michael Torres"),
        None,
        "employees.csv: EMP-200 Michael Torres, email michael.torres@northstar.example.",
    ),
]


def live(kb: str, name: str) -> list[tuple[str, str, int]]:
    """Live entities with this exact name (or any of 'a|b'), richest first."""
    names = ",".join("'" + n.replace("'", "''") + "'" for n in name.split("|"))
    sql = (
        "select e.id, e.canonical_name, (select count(*) from facts f where f.kb_id=e.kb_id and "
        "f.invalidated_at is null and (f.subject_id=e.id or f.object_id=e.id)) n from entities e "
        f"where e.kb_id='{kb}' and e.merged_into is null and e.canonical_name in ({names}) "
        "order by n desc, e.created_at"
    )
    out = subprocess.run(
        [
            "docker",
            "exec",
            DB_CONTAINER,
            "psql",
            "-U",
            "utopia",
            "-d",
            "utopia",
            "-At",
            "-F",
            "\t",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
    ).stdout
    return [
        (r.split("\t")[0], r.split("\t")[1], int(r.split("\t")[2]))
        for r in out.splitlines()
        if r.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the 2026-09-28 identity corrections.")
    parser.add_argument("--apply", action="store_true", help="write to Utopia (default: print)")
    if not parser.parse_args().apply:
        for kb, kind, ref, action, why in PLAN:
            label = ref if isinstance(ref, str) else " → ".join(ref)
            print(f"{kb[-6:]} {kind:6} {action or 'merge':5} {label}  — {why}")
        return
    RUN.mkdir(parents=True, exist_ok=True)
    log = (RUN / "actions.jsonl").open("a")
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (RUN / "started_at.txt").write_text(started + "\n")
    print("correction started", started)
    for kb, kind, ref, action, why in PLAN:
        rec: dict = {"kb": kb, "kind": kind, "ref": ref, "action": action, "rationale": why}
        try:
            if kind == "answer":
                resp = ut.jcall(
                    "POST", f"/kbs/{kb}/review/agent/{ref}", {"action": action, "rationale": why}
                )
            else:
                src_name, tgt_name = ref
                tgts = live(kb, tgt_name)
                srcs = [s for s in live(kb, src_name) if not tgts or s[0] != tgts[0][0]]
                if not srcs or not tgts:
                    raise RuntimeError(f"not found: source={srcs} target={tgts}")
                src, tgt = srcs[-1], tgts[0]  # poorest same-name source → richest target
                rec.update(source=src, target=tgt)
                resp = ut.jcall(
                    "POST",
                    f"/kbs/{kb}/entities/merge",
                    {"source": src[0], "target": tgt[0], "rationale": why},
                )
            rec["result"] = resp
        except SystemExit as e:  # ut.call exits on HTTP error; record and continue
            rec["error"] = str(e)
        except Exception as e:
            rec["error"] = repr(e)
        log.write(json.dumps(rec, ensure_ascii=False) + "\n")
        log.flush()
        label = ref if isinstance(ref, str) else " → ".join(ref)
        print(
            f"{'OK ' if 'error' not in rec else 'ERR'} {kind:6} {action or 'merge':5} {label[:70]}"
            + (f"   {rec.get('error', '')[:160]}" if "error" in rec else "")
        )
    print("correction finished", time.strftime("%Y-%m-%dT%H:%M:%S%z"))


if __name__ == "__main__":
    main()
