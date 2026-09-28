# Discount approval: the decision procedure

You are deciding a discount approval. Follow this procedure. It is the organization's own
process for discount requests: the Sales Discount SOP, which the corpus contains as a
document the knowledge graph did not model.

## Steps

1. **The request.** Identify the request (id, customer, product, requested discount, date,
   requestor) and the basis it relies on: standard pricing, or a customer contract term or
   pricing exception. If the basis can't be determined, say so.
2. **The customer.** CRM account and ERP customer may use different names.
3. **The product,** by SKU.
4. **An active contract:** is there an active customer contract on the request date?
5. **A pricing exception:** is there one covering *this* product on the request date?
6. **The policy** in effect on the request date.
7. **The requestor's approval authority** under that policy.
8. **The required approver:** from the policy's approval bands, the role for this discount
   and who holds it.
9. **Decide,** using exactly one outcome below.
10. **Record** the decision and the evidence relied on.

## Principles

- Contractual eligibility does not change employee authority.
- A request must not be approved solely because a customer contract permits the requested
  discount.
- A pricing exception is scoped to the product and dates it names.
- If a request relies on a contract term that cannot be located, ask for the document before
  deciding.

## Outcomes

| Outcome | When |
|---|---|
| `APPROVE` | Eligibility is established where the request relies on special terms, and the discount is within the requestor's own authority under the policy in force |
| `APPROVE_WITH_AUTHORIZATION` | Eligibility is established, but the discount exceeds the requestor's authority. The approver named by the policy's band for this discount must approve |
| `REJECT_OR_ESCALATE` | The discount exceeds the customer's established eligibility (e.g. above an exception's maximum). A higher approver does not fix this; it needs new or amended terms |
| `REVIEW_REQUIRED` | The request relies on special terms, but none covers this product or date. Special terms do not transfer; it needs commercial review |
| `REQUEST_EVIDENCE` | The request relies on a contract term or exception that no available evidence establishes. Ask for the document before deciding |

## The decision record

End a decision answer with the decision as JSON in a fenced `json` block. Use `null` where
something is unknown, and never guess a value.

```json
{
  "outcome": "APPROVE | APPROVE_WITH_AUTHORIZATION | REJECT_OR_ESCALATE | REVIEW_REQUIRED | REQUEST_EVIDENCE",
  "request": {"id": null, "customer": null, "product": null, "requested_discount": null,
              "date": null, "requestor": null, "basis": "standard | contract_exception | unknown"},
  "commercial_eligibility": {"status": "eligible | exceeded | not_covered | unknown | standard",
                             "maximum_discount": null, "basis": null},
  "authority": {"policy": null, "requestor_limit": null, "requestor_authorized": null,
                "required_role": null, "approver": null},
  "evidence": [],
  "missing_evidence": []
}
```

For a question that is not a discount decision, answer it directly, without the JSON block.
