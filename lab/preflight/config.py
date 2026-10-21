"""The run config (`preflight.yaml`): its models, cross-field rules and the evidence deny-list."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

CheckName = Literal["inputs", "fingerprint", "settled", "agent_context"]

DENIED: tuple[str, ...] = ("dataset/answer-key", "dataset/evaluation", "truth", "site", "owm")
DEFAULT_ERROR_PATTERN = (
    r"(?i)(rate.?limit|\b429\b|insufficient_quota|provider error|upstream error)"
)


class ConfigError(Exception):
    """The run's preflight.yaml is missing or wrong."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InputsConfig(_Model):
    """What the run feeds the system under test."""

    questions: str = "questions.tsv"
    id_patterns: list[str]
    supplied_keys: list[str] = []
    evidence: dict[str, list[str]]

    @model_validator(mode="after")
    def _patterns_compile(self) -> InputsConfig:
        for p in self.id_patterns:
            _compiles(p)
        return self


class Attest(_Model):
    """A hand-written attestation file for a foundation we cannot inspect."""

    file: str
    max_age_hours: float
    covers: list[Literal["jobs", "log", "documents", "commit"]]


class LogSource(_Model):
    """Where a foundation's log lives: a docker container or a file."""

    docker: str | None = None
    file: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> LogSource:
        if (self.docker is None) == (self.file is None):
            raise ValueError("log needs exactly one of docker or file")
        return self


class FoundationConfig(_Model):
    """The foundation under test."""

    kind: Literal["utopia", "b20", "local"]
    arm: str | None = None
    kbs: dict[str, str] | None = None
    db_container: str | None = None
    binary: str | None = None
    log: LogSource | None = None
    attest: Attest | None = None
    error_pattern: str = DEFAULT_ERROR_PATTERN

    @model_validator(mode="after")
    def _kind_needs(self) -> FoundationConfig:
        _compiles(self.error_pattern)
        if self.kind == "utopia":
            for name in ("kbs", "db_container", "binary", "log"):
                if getattr(self, name) is None:
                    raise ValueError(f"a utopia foundation needs {name}")
        if self.kind == "b20" and self.arm is None:
            raise ValueError("a b20 foundation needs arm")
        return self


class SettledConfig(_Model):
    """How long the foundation must be quiet."""

    window_seconds: float = 60


class AgentContextConfig(_Model):
    """The agent-context probe and its spend."""

    probe: list[str]
    est_usd: float
    cap_usd: float


class RunConfig(_Model):
    """One run's pre-flight config."""

    checks: list[CheckName]
    inputs: InputsConfig | None = None
    foundation: FoundationConfig | None = None
    settled: SettledConfig = SettledConfig()
    agent_context: AgentContextConfig | None = None
    baseline: str = "latest"

    @model_validator(mode="after")
    def _listed_checks_have_sections(self) -> RunConfig:
        if "inputs" in self.checks and self.inputs is None:
            raise ValueError("the inputs check is listed but there is no inputs section")
        if {"settled", "fingerprint"} & set(self.checks) and self.foundation is None:
            raise ValueError("settled and fingerprint need a foundation section")
        if "agent_context" in self.checks and self.agent_context is None:
            raise ValueError("the agent_context check is listed but there is no section")
        return self


def _compiles(pattern: str) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"pattern {pattern!r} does not compile: {exc}") from exc


def _check_evidence(cfg: RunConfig, repo: Path) -> None:
    if cfg.inputs is None:
        return
    root = repo.resolve()
    for paths in cfg.inputs.evidence.values():
        for raw in paths:
            full = (root / raw).resolve()
            if not full.is_relative_to(root):
                raise ConfigError(f"evidence path {raw!r} is outside the repo")
            rel = full.relative_to(root)
            if full.name == "MANIFEST.yaml":
                raise ConfigError(f"evidence path {raw!r}: MANIFEST.yaml is never loaded")
            for d in DENIED:
                if rel.is_relative_to(d):
                    raise ConfigError(f"evidence path {raw!r} is deny-listed ({d})")
                if Path(d).is_relative_to(rel):
                    raise ConfigError(f"evidence path {raw!r} contains a deny-listed path ({d})")


def load_config(run: Path, repo: Path) -> RunConfig:
    """Read and validate `run/preflight.yaml`; raise ConfigError naming the problem."""
    path = run / "preflight.yaml"
    if not path.is_file():
        raise ConfigError(f"no preflight.yaml in {run}")
    try:
        cfg = RunConfig.model_validate(yaml.safe_load(path.read_text()))
    except (ValidationError, yaml.YAMLError) as exc:
        raise ConfigError(f"preflight.yaml: {exc}") from exc
    _check_evidence(cfg, repo)
    return cfg
