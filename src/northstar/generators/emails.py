"""Email evidence.

The email names people and a percentage — and says nothing about who may approve.
"""

from __future__ import annotations

from faker import Faker

from northstar.artifacts import Artifact
from northstar.export.markdown import document, pct
from northstar.model import Truth


def generate(truth: Truth, fake: Faker) -> list[Artifact]:
    req = truth.discount_request("DR-9001")
    sender = truth.employee(req.requestor)
    manager = truth.employee(sender.manager or "")
    cust = truth.customer(req.customer)
    prod = truth.product(req.product)
    buyer = fake.first_name()
    domain = truth.organization.email_domain
    body = f"""
**From:** {sender.name} <{sender.email(domain)}>
**To:** {manager.name} <{manager.email(domain)}>
**Date:** {req.request_date.isoformat()} 09:14 CT
**Subject:** Acme {prod.sku} — {req.id}

Hi {manager.preferred_name or manager.first_name},

{buyer} at Acme confirmed this morning they want to move ahead with the {prod.sku} controller
for the third plant. They're asking for {pct(req.requested_discount)} off list, which is what we
did for them last September, and I think their agreement covers it.

I've logged it in CRM as {req.id}. Let me know if you need anything else from me before
Thursday's pipeline review.

Thanks,
{sender.first_name}
"""
    return [
        Artifact(
            id="email_sarah_to_michael",
            path="documents/email_sarah_to_michael.md",
            source_system="Email",
            description=f"Email from the account owner to their manager about {req.id}.",
            content=document(
                {
                    "doc_id": "MSG-20260923-0914",
                    "title": f"Acme {prod.sku} — {req.id}",
                    "from": sender.email(domain),
                    "to": manager.email(domain),
                    "sent": req.request_date.isoformat(),
                },
                body,
            ),
            mentions=("DR-9001", "DR-8104", "EXC-ACME-NS500-15", cust.id),
        )
    ]
