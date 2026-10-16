#!/usr/bin/env node
// LAB WRAPPER (shiny-waffle B-20 baseline, arm A), not part of the bench.
//
// recall.mjs needs a base that already holds the four filings, and on every round it clears the
// facts and re-extracts. For arm A each run is a fresh base built like BlueLeaf's (schema-org +
// w3c-org packs, its flags), the filings are uploaded once, extraction runs once, and the bench's
// own scorer reads the result unchanged: `recall.mjs --kb <id> --score`.
//
// Usage: node recall-armA.mjs --label <name>
// Env: BENCH_BASE, BENCH_EMAIL, BENCH_PASSWORD, BENCH_PSQL (as the bench).

import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.BENCH_BASE || "http://127.0.0.1:1526";
const EMAIL = process.env.BENCH_EMAIL || "bench@test.local";
const PASSWORD = process.env.BENCH_PASSWORD || "benchbench123";
const CORPUS = path.join(HERE, "corpora", "nvda-public-docs");
const truth = JSON.parse(fs.readFileSync(path.join(HERE, "truth", "nvda-public-docs.json"), "utf8"));
const FILES = [...new Set(truth.map((t) => t.doc))].map((d) => `${d}.html`);
const label = process.argv.includes("--label") ? process.argv[process.argv.indexOf("--label") + 1] : "armA";

function psql(sql) {
  const parts = process.env.BENCH_PSQL.split(" ");
  return execFileSync(parts[0], [...parts.slice(1), sql], { encoding: "utf8", maxBuffer: 64 << 20 }).trim();
}
const num = (sql) => Number(psql(sql) || 0);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.error(new Date().toISOString().slice(11, 19), ...a);

let cookie = "";
async function api(method, url, body, isForm) {
  const init = { method, headers: {} };
  if (cookie) init.headers.cookie = cookie;
  if (isForm) init.body = body;
  else if (body !== undefined) { init.headers["content-type"] = "application/json"; init.body = JSON.stringify(body); }
  const r = await fetch(BASE + "/api/v1" + url, init);
  for (const c of r.headers.getSetCookie?.() ?? []) cookie = c.split(";")[0];
  const t = await r.text();
  if (!r.ok) throw new Error(`${method} ${url} -> ${r.status} ${t.slice(0, 200)}`);
  return t ? JSON.parse(t) : null;
}

// Progress, not total time: slow is fine, stalled is not (the bench's rule).
async function drain(kb, what, stallMs = 15 * 60 * 1000) {
  let last = null, deadline = Date.now() + stallMs;
  for (;;) {
    const busy = num(`SELECT count(*) FROM jobs WHERE status IN ('queued','running')
      AND (payload->>'kb_id'='${kb}' OR payload->>'document_id' IN (SELECT id::text FROM documents WHERE kb_id='${kb}'))`);
    // A failed document is finished too: it is reported, not waited on.
    const open = num(`SELECT count(*) FROM documents WHERE kb_id='${kb}' AND deleted_at IS NULL
      AND status <> 'failed' AND (status <> 'ready' OR graph_status IN ('none','queued','extracting'))`);
    const done = num(`SELECT count(c.extracted_at) FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.kb_id='${kb}'`);
    if (busy === 0 && open === 0) return;
    const sig = `${busy}/${open}/${done}`;
    if (sig !== last) { last = sig; deadline = Date.now() + stallMs; log(`${what}: jobs ${busy}, docs open ${open}, chunks extracted ${done}`); }
    if (Date.now() > deadline) throw new Error(`${what}: no progress for ${stallMs / 60000} min`);
    await sleep(10000);
  }
}

await api("POST", "/auth/login", { email: EMAIL, password: PASSWORD });
const ws = (await api("GET", "/workspaces"))[0].id;
const kb = (await api("POST", `/workspaces/${ws}/kbs`, {
  name: `recall ${label} ${new Date().toISOString().slice(0, 16)}`,
  ontology_packs: ["schema-org", "w3c-org"],
})).id;
await api("PATCH", `/kbs/${kb}`, {
  auto_extend_ontology: true, ontology_lang: "en", materialize_inferences: true,
  auto_type_resolution: true, governance: false,
});
log(`base ${kb}`);
await sleep(3000);
await drain(kb, "pack vectors");
for (const f of FILES) {
  const fd = new FormData();
  fd.append("files", new Blob([fs.readFileSync(path.join(CORPUS, f))]), f);
  await api("POST", `/kbs/${kb}/documents`, fd, true);
  log(`uploaded ${f}`);
}
await sleep(5000);
await drain(kb, "extraction");
log(psql(`SELECT string_agg(filename || ' ' || status || '/' || graph_status, '; ') FROM documents WHERE kb_id='${kb}'`));
log(`done; scoring with the bench's scorer`);
console.log(JSON.stringify({ label, kb }));
execFileSync("node", [path.join(HERE, "recall.mjs"), "--kb", kb, "--score"], { stdio: "inherit", env: process.env });
