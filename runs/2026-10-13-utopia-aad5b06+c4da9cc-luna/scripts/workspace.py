"""Create the lab's gpt-6-luna workspace (idempotent) and set its model settings. No key is sent."""
import utopia as u

NAME = "Northstar Lab (gpt-6-luna)"
SHOW = ("chat_base_url", "chat_model", "chat_reasoning_effort", "has_chat_key",
        "embed_base_url", "embed_model", "embed_dim", "has_embed_key")

wss = u.jcall("GET", "/workspaces")
hit = [w for w in wss if w["name"] == NAME]
ws = hit[0] if hit else u.jcall("POST", "/workspaces", {"name": NAME})
wid = ws["id"]
print("workspace:", wid, ws["name"], "(existing)" if hit else "(created)")
s = u.jcall("GET", f"/workspaces/{wid}/settings")
if s.get("chat_model") != "gpt-6-luna":
    body = {"chat_base_url": "https://api.openai.com/v1", "chat_model": "gpt-6-luna",
            "chat_reasoning_effort": "low", "embed_base_url": "https://api.openai.com/v1",
            "embed_model": "text-embedding-3-small", "embed_dim": None}
    print("PUT:", u.jcall("PUT", f"/workspaces/{wid}/settings", body))
    s = u.jcall("GET", f"/workspaces/{wid}/settings")
print({k: s.get(k) for k in SHOW})
