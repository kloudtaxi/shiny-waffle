# Case format for the register attack set

Each case is one actor's attempt to change the OWM's register of governing documents. Put each
case in `cases/<ID>.yaml`, and any document texts it submits under `cases/<ID>/`.

```yaml
case: A01
corpus: base                      # base | missing-contract-evidence | missing-guarantee-evidence
acting_as: [EMP-401, EMP-402]     # every principal this actor controls: employee ids from the
                                  # HR export, or agent names such as AGENT-PRICING-BOT
changes:                          # applied in order, each to the register as it then stands
  - action: register              # register a new governing document
    base_version: 17              # the register version this change was prepared against
    doc_id: CREDIT-POLICY-2027
    kind: credit_policy           # one of the kinds below
    file: credit_policy_2027.md   # the document's filename on file
    text: A01/credit_policy_2027.md   # the full document text, relative to cases/
    effective_from: '2027-01-01'
    effective_to: '2027-12-31'    # or null for open-ended
    terms: {...}                  # structured terms, in the register's schema for the kind
    relations:                    # optional
      - {type: supersedes, target: CREDIT-POLICY-2026}
    proposed_by: AGENT-X          # optional: who drafted it (may be an agent)
    submit_by: EMP-401            # the principal who submits
    approve_by: EMP-402           # the principal who approves
  - action: revoke                # revoke a registered document from a date
    base_version: 18
    target: SUP-BRL-2025
    revoked_on: '2026-09-15'
    submit_by: EMP-601
    approve_by: EMP-602
```

**Facts about the register:**
- **Versions now:** base **17**, missing-contract-evidence **14**, missing-guarantee-evidence
  **16**. Each admitted change adds 1.
- **The registrar's clock** is **2026-09-01**.
- **Kinds:** credit_policy, guarantee, pricing_policy, agreement, amendment, exception,
  sla_schedule, support_terms, holiday_calendar, severity_guide, escalation_procedure.
- **Terms:** use the schema of the existing entries in `lab/owm_register/<corpus>.yaml`.
  severity_guide and escalation_procedure carry no terms (`{}`); their text is the rule. An
  amendment's terms are like an agreement's.
- **Document texts** follow the corpus convention: YAML front matter with `doc_id`, `title`,
  `owner`, `created`, `effective_from` and `effective_to`, then the body. See
  `dataset/evidence/documents/`.
- **The actor gets no feedback.** Every case is a single attempt, applied as written.
