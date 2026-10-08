"""The OWM-served decision context: what an agent gets instead of the whole corpus (G-23).

The OWM assembles it deterministically from the request alone, never from truth or the answer
key:
1. **The served register** for the decision type (`lab/owm_register/serve.py`): the coverage,
   every kind even when empty, the approved terms and the approved text of each governing
   document.
2. **Documents the register names.** The registered pricing policy names the Approval Authority
   Matrix as its operational reference, so discount gets it.
3. **System-of-record rows for this request,** found through the request's own ids:
   - the request's row in its table;
   - the customer's CRM account and ERP customer, joined by DUNS;
   - the employee table (authority is resolved by title and manager);
   - for discount, the product row;
   - for credit, the customer's ERP credit and invoice rows.

The procedure (the system prompt) and the question are unchanged from the reader re-baseline.
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(LAB / "lab/owm_register"))
import serve  # noqa: E402


def rows(root: Path, table: str, keep: Any) -> tuple[list[str], list[dict[str, str]]]:
    with (root / "structured" / f"{table}.csv").open() as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), [x for x in r if keep(x)]


def render(table: str, header: list[str], found: list[dict[str, str]]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    w.writeheader()
    w.writerows(found)
    note = "" if found else "(no rows)\n"
    return f"=== structured/{table}.csv (rows for this request) ===\n{buf.getvalue()}{note}"


def served_slice(kind: str, corpus: str, root: Path, rec: dict[str, Any]) -> str:
    """`kind` is discount or credit; `root` is the scenario's (overlaid) corpus; `rec` the
    request as the question gives it."""
    parts = ["The organization's governing state and records for this decision, as served by "
             "the OWM:", "", serve.served(corpus, kind), ""]  # fmt: skip
    crm_id = rec.get("account_id")
    erp_id = rec.get("erp_customer_id")
    _, crm_all = rows(root, "crm_accounts", lambda x: True)
    _, erp_all = rows(root, "customers", lambda x: True)
    duns = next((x["duns_number"] for x in crm_all if x["account_id"] == crm_id), None) or next(
        (x["duns_number"] for x in erp_all if x["erp_customer_id"] == erp_id), None
    )
    erp_ids = {x["erp_customer_id"] for x in erp_all if x["duns_number"] == duns}
    rid = rec.get("request_id")
    if kind == "discount":
        h, r = rows(root, "discount_requests", lambda x: x["request_id"] == rid)
        parts.append(render("discount_requests", h, r))
    else:
        h, r = rows(root, "credit_requests", lambda x: x["request_id"] == rid)
        parts.append(render("credit_requests", h, r))
    h, r = rows(root, "crm_accounts", lambda x: x["duns_number"] == duns)
    parts.append(render("crm_accounts", h, r))
    h, r = rows(root, "customers", lambda x: x["duns_number"] == duns)
    parts.append(render("customers", h, r))
    h, r = rows(root, "employees", lambda x: True)
    parts.append(render("employees", h, r).replace(" (rows for this request)", ""))
    if kind == "discount":
        h, r = rows(root, "products", lambda x: x["sku"] == rec.get("product_sku"))
        parts.append(render("products", h, r))
        matrix = root / "documents/approval_authority_matrix.md"
        if matrix.exists():
            parts.append(f"=== documents/approval_authority_matrix.md (named by the registered "
                         f"pricing policy) ===\n{matrix.read_text().rstrip()}\n")  # fmt: skip
    else:
        h, r = rows(root, "erp_credit", lambda x: x["erp_customer_id"] in erp_ids)
        parts.append(render("erp_credit", h, r))
        h, r = rows(root, "erp_invoices", lambda x: x["erp_customer_id"] in erp_ids)
        parts.append(render("erp_invoices", h, r))
    return "\n".join(parts)
