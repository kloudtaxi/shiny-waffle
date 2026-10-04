"""Evidence generators: one module per source system (CRM, ERP, Drive, email)."""

from __future__ import annotations

from faker import Faker

from northstar.artifacts import Artifact
from northstar.factories import Background
from northstar.generators import crm, documents, emails, erp, finance, support
from northstar.model import Truth


def generate_evidence(truth: Truth, bg: Background, seed: int) -> list[Artifact]:
    """The full (base) corpus. No single artifact contains a scenario's answer."""
    fake = Faker("en_US")
    fake.seed_instance(seed)
    return [
        *crm.generate(truth, bg),
        *erp.generate(truth, bg),
        *documents.generate(truth, bg, fake),
        *emails.generate(truth, fake),
        *finance.generate(truth, bg),  # experiment 5: last, no shared randomness
        *support.generate(truth, bg),  # experiment 6: after that, no shared randomness
    ]
