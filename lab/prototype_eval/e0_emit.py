"""Spike E0: emit two hand-built traces in today's OTel GenAI and MCP conventions.

The traces have the shape spec §9.7 names (agent turn → MCP tool call → HTTP route → owm.decide →
port calls, one of them a judgment). One trace ends with a decision and one with no decision (a
judgment outage). The values are made up for the spike and hold nothing from Northstar.

The exporter is always built with an explicit endpoint, never from OTEL_EXPORTER_OTLP_* or the
default (on this machine localhost:4318 is sovera-owm's collector).

    python -I e0_emit.py --endpoint URL [--header K=V ...] [--project NAME] [--content]

Prints the two trace ids as hex, one per line.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode

AGENT_MODEL = "claude-sonnet-5-5"
JUDGE_MODEL = "systemone"
QUESTION = "Is a 12% discount on request FH-Q-000123 within the discount policy?"
ANSWER = (
    "It isn't within the rep's authority: 12% is above the 10% limit in the policy in force, so "
    "the decision routes to the sales director for approval. Nothing is applied until then."
)


def _messages(role: str, text: str) -> str:
    return json.dumps([{"role": role, "parts": [{"type": "text", "content": text}]}])


def emit_one(tracer: trace.Tracer, *, decided: bool, content: bool) -> str:
    agent_attrs: dict[str, str | int] = {
        "gen_ai.operation.name": "invoke_agent",
        "gen_ai.agent.name": "owm-reference-agent",
        "gen_ai.provider.name": "anthropic",
        "gen_ai.request.model": AGENT_MODEL,
        "gen_ai.conversation.id": "conv-e0-1" if decided else "conv-e0-2",
    }
    if content:
        agent_attrs["gen_ai.input.messages"] = _messages("user", QUESTION)
        agent_attrs["gen_ai.output.messages"] = _messages(
            "assistant",
            ANSWER
            if decided
            else "The decision service couldn't decide: the "
            "judgment service is unavailable, and operators can fix it. Try again later.",
        )
    with tracer.start_as_current_span(
        "invoke_agent owm-reference-agent", kind=SpanKind.INTERNAL, attributes=agent_attrs
    ) as root:
        with tracer.start_as_current_span(
            f"chat {AGENT_MODEL}",
            kind=SpanKind.CLIENT,
            attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.provider.name": "anthropic",
                "gen_ai.request.model": AGENT_MODEL,
                "gen_ai.usage.input_tokens": 812,
                "gen_ai.usage.output_tokens": 96,
            },
        ):
            pass
        with (
            tracer.start_as_current_span(
                "execute_tool decide",
                kind=SpanKind.INTERNAL,
                attributes={
                    "gen_ai.operation.name": "execute_tool",
                    "gen_ai.tool.name": "decide",
                    "gen_ai.tool.call.id": "toolu_e0_1",
                },
            ),
            tracer.start_as_current_span(
                "tools/call decide",
                kind=SpanKind.SERVER,
                attributes={
                    "mcp.method.name": "tools/call",
                    "mcp.session.id": "mcp-sess-e0",
                    "gen_ai.tool.name": "decide",
                    "jsonrpc.request.id": "7",
                },
            ),
            tracer.start_as_current_span(
                "POST /api/v1/decisions",
                kind=SpanKind.SERVER,
                attributes={
                    "http.request.method": "POST",
                    "http.route": "/api/v1/decisions",
                    "http.response.status_code": 200 if decided else 503,
                },
            ),
        ):
            _decide(tracer, decided=decided)
        with tracer.start_as_current_span(
            f"chat {AGENT_MODEL}",
            kind=SpanKind.CLIENT,
            attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.provider.name": "anthropic",
                "gen_ai.request.model": AGENT_MODEL,
                "gen_ai.usage.input_tokens": 1430,
                "gen_ai.usage.output_tokens": 71,
            },
        ):
            pass
        return format(root.get_span_context().trace_id, "032x")


def _decide(tracer: trace.Tracer, *, decided: bool) -> None:
    with tracer.start_as_current_span(
        "owm.decide discount_approval",
        kind=SpanKind.INTERNAL,
        attributes={"owm.decision.type": "discount_approval"},
    ) as span:
        with tracer.start_as_current_span(
            "owm.port evidence snapshot",
            kind=SpanKind.CLIENT,
            attributes={"owm.port": "evidence", "owm.operation": "snapshot"},
        ):
            pass
        with tracer.start_as_current_span(
            "owm.port records read",
            kind=SpanKind.CLIENT,
            attributes={"owm.port": "records", "owm.operation": "read"},
        ):
            pass
        with tracer.start_as_current_span(
            f"chat {JUDGE_MODEL}",
            kind=SpanKind.CLIENT,
            attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.provider.name": "typesafe",
                "gen_ai.request.model": JUDGE_MODEL,
                "owm.judgment.question": "q-term-fit",
                "owm.judgment.answer_type": "choice",
            },
        ) as judgment:
            if decided:
                judgment.set_attributes(
                    {
                        "gen_ai.usage.input_tokens": 2210,
                        "gen_ai.usage.output_tokens": 12,
                        "owm.judgment.out_of_type": False,
                    }
                )
            else:
                judgment.set_attribute("error.type", "JudgmentUnavailable")
                judgment.set_status(Status(StatusCode.ERROR))
        if decided:
            span.set_attributes(
                {
                    "owm.decision.id": "D-E0-0001",
                    "owm.outcome": "route_to_approver",
                    "owm.procedure.id": "discount",
                    "owm.procedure.version": "2",
                    "owm.pack.version": "1",
                    "owm.profile.version": "1",
                }
            )
        else:
            span.set_attributes(
                {"error.type": "judgment_unavailable", "owm.error.who_can_fix": "operators"}
            )
            span.set_status(Status(StatusCode.ERROR))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--header", action="append", default=[])
    ap.add_argument("--project", default="e0-spike")
    ap.add_argument("--content", action="store_true", help="add GenAI message content (SPAN_ONLY)")
    args = ap.parse_args(argv)
    stray = sorted(k for k in os.environ if k.startswith("OTEL_EXPORTER_OTLP"))
    if stray:
        print(f"refusing: {stray} set; the endpoint must be explicit", file=sys.stderr)
        return 2
    headers = dict(h.split("=", 1) for h in args.header)
    provider = TracerProvider(
        resource=Resource.create(
            {"service.name": "owm-e0-spike", "opik.project_name": args.project}
        )
    )
    provider.add_span_processor(
        SimpleSpanProcessor(OTLPSpanExporter(endpoint=args.endpoint, headers=headers))
    )
    tracer = provider.get_tracer("owm.e0")
    ids = [
        emit_one(tracer, decided=True, content=args.content),
        emit_one(tracer, decided=False, content=args.content),
    ]
    provider.shutdown()
    print("\n".join(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
