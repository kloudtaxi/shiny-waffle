"""Today's foundation's three exam bases, on a throwaway second server (pre-registration §2, D1).

    uv run python lab/exam/today.py check    # the binary, and the repo it was built from
    uv run python lab/exam/today.py db       # create the ephemeral database `utopia_exam`
    uv run python lab/exam/today.py launch   # exec the server on 127.0.0.1:1526, in the background
    uv run python lab/exam/today.py setup --run runs/<exam>    # admin, models, the three bases
    uv run python lab/exam/today.py load --run runs/<exam>     # hash-checked corpora, then wait
    uv run python lab/exam/today.py access --run runs/<exam>   # a read token and a viewer
    uv run python lab/exam/today.py versions --run runs/<exam> # version 1 rows (amendment 4)

As the practice baseline was run (shiny-waffle 3cbf3c2): the live instance's own binary, a second
process on :1526, and its own data directory, against an ephemeral database on the same Postgres
server. The live database is never written: every SQL statement here names `utopia_exam`.

**BlueLeaf's base's settings** (§8.1 of the baseline): packs `schema-org` and `w3c-org`;
`auto_extend_ontology`, `materialize_inferences` and `auto_type_resolution` on; `governance` off;
`ontology_lang` en; `gpt-6-luna` at effort `low` and `text-embedding-3-small`.

**Secrets:** the OpenAI key is read from `_owm-local/bench-openai.key` and only sent to the
instance's settings route. The instance's admin password is random, written once to
`_owm-local/exam-1526-admin.json` (mode 600). The read token and the viewer's password go to
`_owm-local/exam-1526-read.token` and `_owm-local/exam-1526-viewer.json`. None is ever printed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
LOCAL = LAB / "_owm-local"
UTOPIA = Path("/Users/mehulmehta/DEV/Sovera/2026-dev/utopia")
BINARY = UTOPIA / "target/debug/utopia-server"
DB = "utopia_exam"
PORT = 1526
API = f"http://127.0.0.1:{PORT}/api/v1"
STATE = LOCAL / "exam-1526"
ADMIN = LOCAL / "exam-1526-admin.json"
KEY = LOCAL / "bench-openai.key"
CORPUS_COMMIT = "571baac"
HASHES = LAB / "docs/b20-exam-corpus-571baac.sha256"
NAMES = {
    "base": "Northstar Industrial Systems",
    "missing-contract-evidence": "Northstar Industrial Systems — missing contract evidence",
    "missing-guarantee-evidence": "Northstar Industrial Systems — missing guarantee evidence",
}
FOLDERS = {
    "base": "dataset/evidence",
    "missing-contract-evidence": "dataset/evidence-variants/missing-contract-evidence",
    "missing-guarantee-evidence": "dataset/evidence-variants/missing-guarantee-evidence",
}
SETTINGS = {
    "auto_extend_ontology": True,
    "ontology_lang": "en",
    "materialize_inferences": True,
    "auto_type_resolution": True,
    "governance": False,
}


def psql(sql: str, db: str = DB) -> str:
    if db not in (DB, "postgres"):
        raise SystemExit("refusing: the exam only touches utopia_exam")
    out = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "utopia-db-1",
            "psql",
            "-U",
            "utopia",
            "-d",
            db,
            "-X",
            "-q",
            "-tA",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def write_secret(path: Path, data: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(data)


class Api:
    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def call(
        self,
        method: str,
        path: str,
        body: Any = None,
        raw: bytes | None = None,
        ctype: str | None = None,
    ) -> Any:
        data, headers = raw, {}
        if body is not None:
            data, headers = json.dumps(body).encode(), {"content-type": "application/json"}
        if ctype:
            headers["content-type"] = ctype
        req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=300) as r:
                text = r.read().decode()
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path} -> {e.code} {e.read().decode()[:200]}") from None
        return json.loads(text) if text else None

    def login(self) -> None:
        creds = json.loads(ADMIN.read_text())
        self.call("POST", "/auth/login", {"email": creds["email"], "password": creds["password"]})


def cmd_check() -> None:
    head = subprocess.run(
        ["git", "-C", str(UTOPIA), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    diff = subprocess.run(
        ["git", "-C", str(UTOPIA), "diff"], capture_output=True, check=True
    ).stdout
    print(
        json.dumps(
            {
                "utopia_head": head,
                "uncommitted_diff_sha256": hashlib.sha256(diff).hexdigest(),
                "binary": str(BINARY),
                "binary_sha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                "binary_mtime": time.strftime(
                    "%Y-%m-%dT%H:%M:%S%z", time.localtime(BINARY.stat().st_mtime)
                ),
            },
            indent=1,
        )
    )


def cmd_db() -> None:
    if psql(f"SELECT 1 FROM pg_database WHERE datname='{DB}'", "postgres"):
        raise SystemExit(f"{DB} exists already; refusing to reuse it")
    psql(f"CREATE DATABASE {DB}", "postgres")
    psql("CREATE EXTENSION IF NOT EXISTS vector")
    print(f"created {DB}")


def cmd_launch() -> None:
    url = None
    for line in (UTOPIA / ".env").read_text().splitlines():
        if line.startswith("UTOPIA_DATABASE_URL="):
            url = line.split("=", 1)[1].strip().strip("\"'")
    if not url:
        raise SystemExit("no UTOPIA_DATABASE_URL in the live .env")
    from urllib.parse import urlsplit, urlunsplit

    p = urlsplit(url)
    if p.path.strip("/") != "utopia":
        raise SystemExit("unexpected live database name; refusing")
    for d in ("data", "run"):
        (STATE / d).mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("UTOPIA_")}
    env.update(
        {
            "UTOPIA_DATABASE_URL": urlunsplit((p.scheme, p.netloc, f"/{DB}", p.query, p.fragment)),
            "UTOPIA_BIND_ADDR": f"127.0.0.1:{PORT}",
            "UTOPIA_DATA_DIR": str(STATE / "data"),
            "UTOPIA_OPEN_REGISTRATION": "true",
        }
    )
    os.chdir(STATE / "run")
    os.execve(str(BINARY), ["utopia-server"], env)


def drain(kb: str, what: str, stall_s: int = 900) -> None:
    """Progress, not total time: slow is fine, stalled is not (the baseline's rule)."""
    last, deadline = "", time.time() + stall_s
    while True:
        busy = psql(
            "SELECT count(*) FROM jobs WHERE status IN ('queued','running') AND ("
            f"payload->>'kb_id'='{kb}' OR payload->>'document_id' IN "
            f"(SELECT id::text FROM documents WHERE kb_id='{kb}'))"
        )
        open_ = psql(
            f"SELECT count(*) FROM documents WHERE kb_id='{kb}' AND deleted_at IS NULL"
            " AND status <> 'failed'"
            " AND (status <> 'ready' OR graph_status IN ('none','queued','extracting'))"
        )
        if busy == "0" and open_ == "0":
            return
        sig = f"{busy}/{open_}"
        if sig != last:
            last, deadline = sig, time.time() + stall_s
            print(
                f"{time.strftime('%H:%M:%S')} {what}: jobs {busy}, documents open {open_}",
                flush=True,
            )
        if time.time() > deadline:
            raise SystemExit(f"{what}: no progress for {stall_s // 60} min")
        time.sleep(10)


def bases_file(run: Path) -> Path:
    return run / "today-bases.json"


def cmd_setup(run: Path) -> None:
    if bases_file(run).exists():
        raise SystemExit(f"{bases_file(run)} exists: the bases are made once")
    api = Api()
    email = "exam-admin@lab.local"
    write_secret(ADMIN, json.dumps({"email": email, "password": secrets.token_urlsafe(24)}) + "\n")
    creds = json.loads(ADMIN.read_text())
    api.call(
        "POST",
        "/auth/register",
        {"email": email, "password": creds["password"], "display_name": "exam", "org_name": "exam"},
    )
    api.login()
    ws = api.call("GET", "/workspaces")[0]["id"]
    key = KEY.read_text().strip()
    api.call(
        "PUT",
        f"/workspaces/{ws}/settings",
        {
            "chat_base_url": "https://api.openai.com/v1",
            "chat_api_key": key,
            "chat_model": "gpt-6-luna",
            "chat_reasoning_effort": "low",
            "embed_base_url": "https://api.openai.com/v1",
            "embed_api_key": key,
            "embed_model": "text-embedding-3-small",
        },
    )
    del key
    settings = api.call("GET", f"/workspaces/{ws}/settings")
    kbs = {}
    for corpus, name in NAMES.items():
        kb = api.call(
            "POST",
            f"/workspaces/{ws}/kbs",
            {"name": name, "ontology_packs": ["schema-org", "w3c-org"]},
        )["id"]
        api.call("PATCH", f"/kbs/{kb}", SETTINGS)
        kbs[corpus] = kb
    for corpus, kb in kbs.items():
        drain(kb, f"{corpus}: pack vectors")
    record = {
        "workspace": ws,
        "kbs": kbs,
        "names": NAMES,
        "settings": SETTINGS,
        "models": {
            k: settings.get(k) for k in ("chat_model", "chat_reasoning_effort", "embed_model")
        },
        "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    bases_file(run).write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(record, indent=1, ensure_ascii=False))


def corpus_files(corpus: str) -> list[tuple[str, bytes]]:
    """The corpus at 571baac, every file checked against the hash list before anything is sent."""
    want = {}
    for line in HASHES.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        c, h, rel = line.split(None, 2)
        if c == corpus:
            want[rel] = h
    listed = subprocess.run(
        [
            "git",
            "-C",
            str(LAB),
            "ls-tree",
            "-r",
            "--name-only",
            CORPUS_COMMIT,
            FOLDERS[corpus] + "/",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    got = {}
    for path in listed:
        rel = path[len(FOLDERS[corpus]) + 1 :]
        if (rel.startswith("documents/") and rel.endswith(".md")) or (
            rel.startswith("structured/") and rel.endswith(".csv")
        ):
            data = subprocess.run(
                ["git", "-C", str(LAB), "show", f"{CORPUS_COMMIT}:{path}"],
                capture_output=True,
                check=True,
            ).stdout
            got[rel] = data
    have = {rel: hashlib.sha256(b).hexdigest() for rel, b in got.items()}
    if have != want:
        raise SystemExit(f"{corpus}: the files don't match the hash list; nothing uploaded")
    return sorted(got.items())


def cmd_load(run: Path) -> None:
    rec = json.loads(bases_file(run).read_text())
    plan = {c: corpus_files(c) for c in NAMES}  # every corpus checked before the first upload
    api = Api()
    api.login()
    for corpus, files in plan.items():
        kb = rec["kbs"][corpus]
        for rel, data in files:
            name = rel.rsplit("/", 1)[-1]
            boundary = uuid.uuid4().hex
            mime = "text/csv" if name.endswith(".csv") else "text/markdown"
            body = (
                (
                    f"--{boundary}\r\nContent-Disposition: form-data; "
                    f'name="file"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'
                ).encode()
                + data
                + f"\r\n--{boundary}--\r\n".encode()
            )
            api.call(
                "POST",
                f"/kbs/{kb}/documents",
                raw=body,
                ctype=f"multipart/form-data; boundary={boundary}",
            )
        print(f"{corpus}: {len(files)} files uploaded", flush=True)
    for corpus in plan:
        drain(rec["kbs"][corpus], f"{corpus}: extraction")
    summary = {
        c: psql(
            "SELECT count(*) || ' documents, ' || count(*) FILTER (WHERE status='failed' OR "
            f"graph_status='failed') || ' failed' FROM documents WHERE kb_id='{rec['kbs'][c]}'"
        )
        for c in plan
    }
    print(json.dumps(summary, indent=1))


def cmd_access(run: Path) -> None:
    rec = json.loads(bases_file(run).read_text())
    api = Api()
    api.login()
    kbs = list(rec["kbs"].values())
    tok = api.call(
        "POST",
        "/me/tokens",
        {"name": "exam-adapter-read", "scope": "read", "kb_ids": kbs, "expires_in_days": 7},
    )
    write_secret(LOCAL / "exam-1526-read.token", tok["token"] + "\n")
    email, password = "exam-viewer@lab.local", secrets.token_urlsafe(18)
    user = api.call(
        "POST",
        "/admin/users",
        {"email": email, "password": password, "display_name": "exam viewer", "role": "viewer"},
    )
    api.call(
        "PUT", f"/workspaces/{rec['workspace']}/members/{user['user']['id']}", {"role": "viewer"}
    )
    write_secret(
        LOCAL / "exam-1526-viewer.json",
        json.dumps({"base": f"http://127.0.0.1:{PORT}", "email": email, "password": password})
        + "\n",
    )
    print(
        json.dumps(
            {
                "read_token": "_owm-local/exam-1526-read.token",
                "token_kbs": len(kbs),
                "viewer": "_owm-local/exam-1526-viewer.json",
                "workspace": rec["workspace"],
            },
            indent=1,
        )
    )


def cmd_versions(run: Path) -> None:
    """Amendment 4: today's foundation records no version for a file upload (`create_from_upload`
    writes the document row only), and the adapter serves a document's text, passages and search
    hits only for a recorded version. So each exam document without one gets its version 1, as
    today's own `record_version` writes it when it adopts an older document: its own sha256 and
    size, and its doc_time; received when it was uploaded. Nothing extracted is touched."""
    rec = json.loads(bases_file(run).read_text())
    kbs = ",".join(f"'{kb}'" for kb in rec["kbs"].values())
    before = psql(
        f"SELECT count(*) FROM document_versions v JOIN documents d ON d.id = v.document_id"
        f" WHERE d.kb_id IN ({kbs})"
    )
    if before != "0":
        raise SystemExit(f"{before} version rows exist already; refusing")
    psql(
        "INSERT INTO document_versions (id, document_id, version, sha256, size_bytes,"
        " ingested_at, doc_time)"
        " SELECT gen_random_uuid(), d.id, 1, d.sha256, d.size_bytes, d.created_at, d.doc_time"
        f" FROM documents d WHERE d.kb_id IN ({kbs})"
    )
    out = {
        corpus: psql(
            "SELECT count(*) || ' documents, ' || count(v.id) || ' with version 1'"
            " FROM documents d LEFT JOIN document_versions v"
            f" ON v.document_id = d.id AND v.version = 1 WHERE d.kb_id = '{kb}'"
        )
        for corpus, kb in rec["kbs"].items()
    }
    print(json.dumps(out, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(prog="exam-today")
    ap.add_argument("cmd", choices=["check", "db", "launch", "setup", "load", "access", "versions"])
    ap.add_argument("--run", type=Path)
    a = ap.parse_args()
    if a.cmd in ("setup", "load", "access", "versions") and not a.run:
        raise SystemExit("--run is needed")
    if a.cmd == "check":
        cmd_check()
    elif a.cmd == "db":
        cmd_db()
    elif a.cmd == "launch":
        cmd_launch()
    elif a.cmd == "setup":
        cmd_setup(a.run.resolve())
    elif a.cmd == "load":
        cmd_load(a.run.resolve())
    elif a.cmd == "access":
        cmd_access(a.run.resolve())
    else:
        cmd_versions(a.run.resolve())
    sys.exit(0)


if __name__ == "__main__":
    main()
