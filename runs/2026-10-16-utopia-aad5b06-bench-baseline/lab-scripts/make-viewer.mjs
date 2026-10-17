// Create a read-only (viewer) account on the throwaway bench instance (:1526) for web-next's
// reference check, add it to the bench workspace as viewer, prove it reads and cannot write,
// and write its login to a local gitignored file (O_EXCL, mode 600). The password is random
// and never printed. Usage: node make-viewer.mjs OUT_FILE
import fs from "node:fs";
import crypto from "node:crypto";
const BASE = "http://127.0.0.1:1526/api/v1";
const [outFile] = process.argv.slice(2);
function client() {
  let cookie = "";
  return async function api(method, url, body, quiet) {
    const init = { method, headers: {} };
    if (cookie) init.headers.cookie = cookie;
    if (body !== undefined) { init.headers["content-type"] = "application/json"; init.body = JSON.stringify(body); }
    const r = await fetch(BASE + url, init);
    for (const c of r.headers.getSetCookie?.() ?? []) cookie = c.split(";")[0];
    const t = await r.text();
    if (quiet) return r.status;
    if (!r.ok) throw new Error(`${method} ${url} -> ${r.status} ${t.slice(0, 200)}`);
    return t ? JSON.parse(t) : null;
  };
}
const email = "webnext-viewer@test.local";
const password = crypto.randomBytes(18).toString("base64url");
const admin = client();
await admin("POST", "/auth/login", { email: "bench@test.local", password: "benchbench123" });
const ws = (await admin("GET", "/workspaces"))[0].id;
const { user } = await admin("POST", "/admin/users", {
  email, password, display_name: "web-next viewer (B-20 reference check)", role: "viewer",
});
await admin("PUT", `/workspaces/${ws}/members/${user.id}`, { role: "viewer" });
// Write the file before the checks, so a failed check never leaves an account with a lost password.
const fd = fs.openSync(outFile, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL, 0o600);
fs.writeSync(fd, JSON.stringify({ base: "http://127.0.0.1:1526", email, password }, null, 1) + "\n");
fs.closeSync(fd);
const viewer = client();
await viewer("POST", "/auth/login", { email, password });
const kb = "01a14691-2cbb-75c3-abfc-fbae9a32d368"; // recall arm A run 1
const read = await viewer("GET", `/kbs/${kb}/ontology`, undefined, true);
const write = await viewer("PATCH", `/kbs/${kb}`, { governance: true }, true);
const settings = await viewer("PUT", `/workspaces/${ws}/settings`, { chat_model: "x" }, true);
console.log(JSON.stringify({ user_id: user.id, workspace_role: "viewer", read_status: read,
  patch_kb_status: write, put_settings_status: settings, file_written: true }));
