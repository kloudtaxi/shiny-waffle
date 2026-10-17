// Mint a read-only personal token on the throwaway bench instance (:1526), narrowed to the
// baseline's bases, and write it to a local gitignored file (O_EXCL, mode 600).
// Prints only the token's prefix length and its info, never the token.
// Usage: node mint-read-token.mjs DIGEST_JSON OUT_FILE
import fs from "node:fs";
const BASE = "http://127.0.0.1:1526/api/v1";
const [digestPath, outFile] = process.argv.slice(2);
let cookie = "";
async function api(method, url, body) {
  const init = { method, headers: {} };
  if (cookie) init.headers.cookie = cookie;
  if (body !== undefined) { init.headers["content-type"] = "application/json"; init.body = JSON.stringify(body); }
  const r = await fetch(BASE + url, init);
  for (const c of r.headers.getSetCookie?.() ?? []) cookie = c.split(";")[0];
  const t = await r.text();
  if (!r.ok) throw new Error(`${method} ${url} -> ${r.status} ${t.slice(0, 200)}`);
  return t ? JSON.parse(t) : null;
}
const d = JSON.parse(fs.readFileSync(digestPath, "utf8"));
const kbs = new Set();
for (const r of Object.values(d.temporal)) kbs.add(r.kb);
for (const r of Object.values(d.identity)) { kbs.add(r.forward.kb); kbs.add(r.reverse.kb); }
for (const r of Object.values(d.recall)) kbs.add(r.kb);
for (const r of Object.values(d.contracts)) kbs.add(r.kb);
await api("POST", "/auth/login", { email: "bench@test.local", password: "benchbench123" });
const res = await api("POST", "/me/tokens", {
  name: "b20-baseline-read (garbanzo adapter)", scope: "read", kb_ids: [...kbs], expires_in_days: 7,
});
const fd = fs.openSync(outFile, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL, 0o600);
fs.writeSync(fd, res.token + "\n");
fs.closeSync(fd);
const { info } = res;
console.log(JSON.stringify({ written: true, token_length: res.token.length, scope: info.scope,
  kb_count: (info.kb_ids || []).length, expires_at: info.expires_at, name: info.name }));
