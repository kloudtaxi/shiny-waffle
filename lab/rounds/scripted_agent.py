"""A deterministic stand-in for the Claude agent: it drives the same `deal_desk` tools server.

`scripted(steps, service_url)` returns an `AgentFn`. Each arm has a list of steps, `(tool, args)`,
`("human", {})` (Sarah resolves the condition, Michael approves, over HTTP) or `("crash", {})`.
The tools server is started from the call's MCP config exactly as Claude Code would start it, so
tests exercise the real server. The transcript is stream-json, like the real agent's, and opens
with an `init` event that reports every configured server (`kb` too, when there is one) as
connected unless told otherwise. No spend.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from typing import Any

from rounds.agent import AgentCall, AgentFn, AgentResult

Step = tuple[str, dict[str, Any]]


def _expand_env(spec_env: dict[str, str], env: dict[str, str]) -> dict[str, str]:
    """Each value must be exactly `${<its own key>}`; the value comes from `env` or we raise."""
    out: dict[str, str] = {}
    for key, ref in spec_env.items():
        if ref != "${" + key + "}":
            raise RuntimeError(f"bad env reference: {key}")
        if key not in env:
            raise RuntimeError(f"missing env: {key}")
        out[key] = env[key]
    return out


def _post(base: str, path: str, body: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        base.rstrip("/") + path, data=json.dumps(body).encode(), method="POST", headers=headers
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out: dict[str, Any] = json.loads(resp.read())
        return out


def _human(service_url: str, decision: dict[str, Any]) -> None:
    """Sarah confirms the record (condition c1), then Michael approves."""
    did = decision["decision_id"]
    sarah = str(_post(service_url, "/lab/sessions", {"person_id": "EMP-101"})["token"])
    michael = str(_post(service_url, "/lab/sessions", {"person_id": "EMP-200"})["token"])
    resolved = _post(
        service_url,
        f"/api/v1/decisions/{did}/conditions/c1/resolve",
        {"decision_version": decision["version"], "resolution": "confirmed_record"},
        sarah,
    )
    _post(
        service_url,
        f"/api/v1/decisions/{did}/approve",
        {"decision_version": resolved["version"]},
        michael,
    )


class _Server:
    def __init__(self, call: AgentCall) -> None:
        spec = call.mcp_config["mcpServers"]["deal_desk"]
        env = {**os.environ, **_expand_env(spec.get("env", {}), call.env)}
        self.proc = subprocess.Popen(
            [spec["command"], *spec["args"]],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
        )
        self._id = 0
        try:
            self.rpc("initialize", {})
            self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except BaseException:
            self.close()
            raise

    def send(self, msg: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._id += 1
        self.send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        assert self.proc.stdout is not None
        reply: dict[str, Any] = json.loads(self.proc.stdout.readline())
        return reply

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        if self.proc.stdout is not None:
            self.proc.stdout.close()


def scripted(
    steps: dict[str, list[Step]],
    service_url: str,
    cost_usd: float = 0.0,
    servers: dict[str, str] | None = None,
) -> AgentFn:
    """The steps run are `steps[ROUNDS_STEPS]` when that env var is set (a B-19 finish scripts each
    turn), else `steps[ROUNDS_ARM]`.

    `servers` overrides the status the `init` event reports for a server (else "connected").
    The steps still run: a test of a server that failed decides what the steps do."""

    def run(call: AgentCall) -> AgentResult:
        status = {n: (servers or {}).get(n, "connected") for n in call.mcp_config["mcpServers"]}
        init = {"type": "system", "subtype": "init",
                "mcp_servers": [{"name": n, "status": s} for n, s in status.items()]}  # fmt: skip
        lines: list[str] = [json.dumps(init)]
        turns = 0
        last_decide: dict[str, Any] | None = None
        server = _Server(call)
        try:
            for tool, args in steps[call.env.get("ROUNDS_STEPS") or call.env["ROUNDS_ARM"]]:
                if tool == "crash":
                    transcript = "\n".join(lines)
                    return AgentResult(transcript, None, 0.0, turns, "crashed", "crashed", status)
                if tool == "human":
                    if last_decide is None:
                        raise RuntimeError("human step before any decide")
                    _human(service_url, last_decide)
                    continue
                turns += 1
                block = {"type": "tool_use", "name": f"mcp__deal_desk__{tool}", "input": args}
                lines.append(json.dumps({"type": "assistant", "message": {"content": [block]}}))
                out = server.rpc("tools/call", {"name": tool, "arguments": args})["result"]
                text = out["content"][0]["text"]
                result = {"type": "tool_result", "content": text, "is_error": out["isError"]}
                lines.append(json.dumps({"type": "user", "message": {"content": [result]}}))
                if tool == "decide" and not out["isError"]:
                    last_decide = json.loads(text)
        finally:
            server.close()
        final = {
            "type": "result",
            "subtype": "success",
            "num_turns": turns,
            "total_cost_usd": cost_usd,
            "result": "scripted",
        }
        lines.append(json.dumps(final))
        return AgentResult("\n".join(lines), "scripted", cost_usd, turns, "success", None, status)

    return run
