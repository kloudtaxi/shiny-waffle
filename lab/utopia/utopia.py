"""A small Utopia REST client for the Northstar experiment. Standard library only.

    python3 lab/utopia/utopia.py create-kb "Northstar Industrial Systems" schema-org w3c-org
    python3 lab/utopia/utopia.py upload <kb-id> dataset/evidence/structured/*.csv ...
    python3 lab/utopia/utopia.py export <kb-id> runs/<run>/snapshot/base.ttl
    python3 lab/utopia/utopia.py get /kbs/<kb-id>/review/summary
    python3 lab/utopia/utopia.py ask <kb-id> S01 "<question>" runs/<run>/answers   # arm A
    python3 lab/utopia/utopia.py delete-kb <kb-id>

Configuration comes from the environment:

    UTOPIA_API        default http://localhost:1516/api/v1
    UTOPIA_EMAIL      login for the REST session (the JWT lives in memory only)
    UTOPIA_PASSWORD
    UTOPIA_WORKSPACE  workspace for create-kb; default: the first one the user can see

Without UTOPIA_EMAIL / UTOPIA_PASSWORD, the login is read from the gitignored
`_owm-local/utopia-getting-started.md`. Nothing secret is written to disk or printed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
API = os.environ.get("UTOPIA_API", "http://localhost:1516/api/v1")
LOCAL_NOTES = LAB / "_owm-local" / "utopia-getting-started.md"


def _creds() -> tuple[str, str]:
    email, password = os.environ.get("UTOPIA_EMAIL"), os.environ.get("UTOPIA_PASSWORD")
    if email and password:
        return email, password
    if not LOCAL_NOTES.exists():
        sys.exit("Set UTOPIA_EMAIL and UTOPIA_PASSWORD (or keep them in _owm-local/).")
    text = LOCAL_NOTES.read_text()
    m_email = re.search(r"^\*\*email:\*\*\s*`([^`]+)`", text, re.M)
    m_pw = re.search(r"^\*\*password:\*\*\s*`([^`]+)`", text, re.M)
    if not (m_email and m_pw):
        sys.exit(f"No **email:** / **password:** lines in {LOCAL_NOTES.name}.")
    return m_email.group(1), m_pw.group(1)


_TOKEN: str | None = None


def token() -> str:
    """The session JWT; REST routes want it (a utp_pat_ token only works for MCP and reads)."""
    global _TOKEN
    if _TOKEN is None:
        email, password = _creds()
        body = json.dumps({"email": email, "password": password}).encode()
        req = urllib.request.Request(
            f"{API}/auth/login", body, {"content-type": "application/json"}, method="POST"
        )
        _TOKEN = json.load(urllib.request.urlopen(req))["token"]
    return _TOKEN


def call(
    method: str,
    path: str,
    data: object = None,
    raw: bytes | None = None,
    ctype: str | None = None,
    timeout: float = 120,
) -> Any:
    headers = {"Authorization": f"Bearer {token()}"}
    body = raw
    if data is not None:
        body = json.dumps(data).encode()
        headers["content-type"] = "application/json"
    if ctype:
        headers["content-type"] = ctype
    req = urllib.request.Request(f"{API}{path}", body, headers, method=method)
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code} {e.read().decode()[:400]}") from e


def jcall(method: str, path: str, data: object = None) -> Any:
    text = call(method, path, data).read().decode()
    return json.loads(text) if text else None


def workspace() -> str:
    ws = os.environ.get("UTOPIA_WORKSPACE")
    if ws:
        return ws
    spaces = jcall("GET", "/workspaces")
    if not spaces:
        sys.exit("No workspace visible to this user; set UTOPIA_WORKSPACE.")
    return str(spaces[0]["id"])


def create_kb(name: str, packs: list[str]) -> None:
    body = {"name": name, "ontology_packs": packs}
    kb = jcall("POST", f"/workspaces/{workspace()}/kbs", body)
    print(json.dumps({k: kb.get(k) for k in ("id", "name", "kind", "created_at")}))


def delete_kb(kb: str) -> None:
    call("DELETE", f"/kbs/{kb}")
    print("deleted", kb)


def upload(kb: str, files: list[str]) -> None:
    """One multipart request per file, so each response names what happened to it."""
    for f in files:
        p = Path(f)
        boundary = uuid.uuid4().hex
        mime = "text/csv" if p.suffix == ".csv" else "text/markdown"
        head = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{p.name}"\r\nContent-Type: {mime}\r\n\r\n'
        ).encode()
        body = head + p.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        resp = call(
            "POST",
            f"/kbs/{kb}/documents",
            raw=body,
            ctype=f"multipart/form-data; boundary={boundary}",
        )
        print(p.name, resp.read().decode()[:300])


def export(kb: str, out: str) -> None:
    """The RDF export (Turtle): Utopia's declared machine-readable read contract."""
    data = call("GET", f"/kbs/{kb}/export?format=turtle", timeout=600).read()
    Path(out).write_bytes(data)
    print(out, len(data), "bytes")


def get(path: str) -> None:
    print(json.dumps(jcall("GET", path), indent=2, ensure_ascii=False))


def _parse_sse(resp: Any) -> tuple[list[str], list[tuple[str, str]]]:
    raw_lines: list[str] = []
    frames: list[tuple[str, str]] = []
    event, data = "message", []
    for line in resp:
        s = line.decode("utf-8", "replace").rstrip("\n").rstrip("\r")
        raw_lines.append(s)
        if s.startswith("event:"):
            event = s[6:].strip()
        elif s.startswith("data:"):
            data.append(s[5:].lstrip(" "))
        elif s == "":
            if data:
                frames.append((event, "\n".join(data)))
                if event in ("done", "error"):
                    break
            event, data = "message", []
    return raw_lines, frames


def ask(kb: str, sid: str, question: str, outdir: str) -> None:
    """Arm A: one question to Utopia's in-app chat, in a new conversation. Saves the raw SSE,
    a readable answer with the tool steps, and the stored conversation."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    resp = call("POST", f"/kbs/{kb}/chat", {"message": question}, timeout=900)
    raw_lines, frames = _parse_sse(resp)
    (out / f"{sid}.sse").write_text("\n".join(raw_lines) + "\n")

    conv_id = None
    answer: list[str] = []
    steps: list[Any] = []
    sources: list[Any] = []
    errors: list[Any] = []
    for ev, d in frames:
        try:
            obj: Any = json.loads(d)
        except json.JSONDecodeError:
            obj = d
        if ev == "conversation":
            conv_id = obj.get("id")
        elif ev == "delta":
            answer.append(obj.get("text", ""))
        elif ev == "step":
            steps.append(obj)
        elif ev == "sources":
            sources.append(obj)
        elif ev == "error":
            errors.append(obj)

    detail = jcall("GET", f"/kbs/{kb}/conversations/{conv_id}") if conv_id else None
    conv_json = json.dumps(detail, indent=2, ensure_ascii=False) + "\n"
    (out / f"{sid}.conversation.json").write_text(conv_json)

    md = [
        f"# {sid}",
        "",
        f"- KB: `{kb}`",
        f"- Conversation: `{conv_id}`",
        f"- Asked: {started}",
        "",
        "## Question (verbatim)",
        "",
        f"> {question}",
        "",
        "## Answer",
        "",
        "".join(answer).strip() or "_(no text)_",
        "",
        "## Tool steps",
        "",
    ]
    md += ["- `" + json.dumps(st, ensure_ascii=False)[:600] + "`" for st in steps]
    if sources:
        md += ["", "## Sources", ""]
        md += ["- `" + json.dumps(s, ensure_ascii=False)[:1500] + "`" for s in sources]
    if errors:
        md += ["", "## Errors", ""]
        md += [f"- `{json.dumps(e, ensure_ascii=False)}`" for e in errors]
    (out / f"{sid}.md").write_text("\n".join(md) + "\n")
    chars = len("".join(answer))
    print(f"{sid}: {chars} chars, {len(steps)} steps, {len(errors)} errors, conv {conv_id}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="utopia", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-kb", help="create a knowledge base with ontology packs")
    p.add_argument("name")
    p.add_argument("packs", nargs="*", help="pack ids, in order (schema-org first)")
    sub.add_parser("delete-kb").add_argument("kb")
    p = sub.add_parser("upload", help="upload files to a knowledge base")
    p.add_argument("kb")
    p.add_argument("files", nargs="+")
    p = sub.add_parser("export", help="save the RDF (Turtle) export")
    p.add_argument("kb")
    p.add_argument("out")
    sub.add_parser("get", help="GET any /api/v1 path").add_argument("path")
    p = sub.add_parser("ask", help="arm A: ask Utopia's in-app chat one question")
    p.add_argument("kb")
    p.add_argument("sid")
    p.add_argument("question")
    p.add_argument("outdir")
    a = parser.parse_args()
    if a.cmd == "create-kb":
        create_kb(a.name, a.packs)
    elif a.cmd == "delete-kb":
        delete_kb(a.kb)
    elif a.cmd == "upload":
        upload(a.kb, a.files)
    elif a.cmd == "export":
        export(a.kb, a.out)
    elif a.cmd == "get":
        get(a.path)
    else:
        ask(a.kb, a.sid, a.question, a.outdir)


if __name__ == "__main__":
    main()
