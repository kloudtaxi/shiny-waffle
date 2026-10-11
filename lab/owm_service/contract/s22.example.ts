/**
 * S22 end to end (contract-v1.2.md §10), typed against the contract so the
 * document's JSON can't drift from it. The kernel's part is S22's replay at
 * shiny-waffle deebdd8 (PROC-DISCOUNT v1); conditions, versions and
 * clearances are the service's. Times are illustrative. Revised after the
 * lab's review and re-review: truth field names, the subject's floor, the
 * session's actor, DC-6, and `spent` keyed to the subject.
 */
import type {
  Actor,
  ClearanceRequest,
  ClearanceResponse,
  DecisionRecord,
  Judgment,
  PersonRef,
  DecisionRequest,
  Execution,
  RedeemResponse,
  Refusals,
} from "./owm-decisions";

const sarah: PersonRef = { id: "EMP-101", name: "Sarah Chen", title: "Enterprise Account Executive", function: "Sales" };
const michael: PersonRef = { id: "EMP-200", name: "Michael Torres", title: "VP Sales", function: "Sales" };

const dealDesk: Actor = {
  kind: "agent",
  id: "AGT-DEALDESK",
  name: "Deal Desk Agent",
  version: "9c1e…",
  on_behalf_of: sarah,
  mandate: { doc_id: "MANDATE-DEALDESK-2026" },
};

const role = (choice: string): Judgment => ({
  q: "role",
  about: null,
  form: "choice",
  choice,
  probabilities: { [choice]: 1.0 },
  confidence: 1.0,
  uncertain: false,
});
const party = (p: number, confidence: number): Judgment => ({
  q: "party",
  about: null,
  form: "choice",
  choice: "same_legal_entity",
  probabilities: { same_legal_entity: p, unclear: Math.round((1 - p) * 100) / 100 },
  confidence,
  uncertain: false,
});
const covers = (p: number): Judgment => ({ q: "covers_product", about: null, form: "yes_no", yes: true, p_yes: p, uncertain: false });

/** The 14 judgments, in the kernel's order. */
const judgments: Judgment[] = [
  role("enterprise_account_executive"),
  role("vp_sales"),
  { q: "basis", about: null, form: "choice", choice: "contract_terms", probabilities: { contract_terms: 1.0 }, confidence: 1.0, uncertain: false },
  party(0.96, 0.94),
  covers(0.98),
  party(0.99, 0.98),
  covers(0.98),
  party(0.98, 0.97),
  covers(0.96),
  party(0.99, 0.98),
  covers(0.98),
  role("enterprise_account_executive"),
  role("vp_sales"),
  role("chief_revenue_officer"),
];

const params15 = { request_id: "DR-9001", account_id: "CRM-2048", product: "NS-500", discount: 0.15 };

/** Step 1: the body names the subject and the submitted figure, nothing else. No as_of. */
export const ask: DecisionRequest = {
  decision_type: "discount",
  subject: { request_id: "DR-9001" },
  submitted: { requested_discount: 0.08 },
};

export const v1: DecisionRecord = {
  decision_id: "DEC-0418",
  version: 1,
  decision_type: "discount",
  subject: { request_id: "DR-9001", account_id: "CRM-2048", product: "NS-500" },
  submitted: { requested_discount: 0.08 },
  requested_by: sarah,
  actor: dealDesk,
  requested_at: "2026-09-23T10:02:00-05:00",
  as_of: "2026-09-23",
  decided_at: "2026-09-23T10:02:01-05:00",
  decided_by: {
    kind: "owm",
    procedure: { id: "PROC-DISCOUNT", version: 1, sha256: "f49c4a681783ca4ca198cbdb8a5e4568e5ffa4f94d80ba24e2f738d792e8c694" },
    judgments: 14,
    uncertain: 0,
  },
  outcome: "APPROVE_WITH_AUTHORIZATION",
  gated_outcome: "APPROVE_WITH_AUTHORIZATION",
  routed: false,
  findings: {
    type: "discount",
    commercial_eligibility: { status: "eligible", maximum_discount: 0.15, basis: "EXC-ACME-NS500-15" },
    authority: {
      policy: "PRICING-POLICY-2026",
      requestor_limit: 0.1,
      requestor_authorized: false,
      required_role: "VP Sales",
      approver: michael,
    },
  },
  judgments,
  flags: [],
  conditions: [
    {
      id: "c1",
      source: "input_conflict",
      what: "Confirm the discount on DR-9001: submitted 8%, the CRM says 15%. The decision is on the CRM's 15%.",
      who: [sarah],
      blocking: true,
      field: "requested_discount",
      submitted: 0.08,
      on_record: 0.15,
      opened_in_version: 1,
      resolved: null,
    },
  ],
  approvals: [{ kind: "approval", role: "VP Sales", person: michael, passed_from: null, given: null, declined: null }],
  actions: [{ action: "apply_discount", params: params15, expected_actor: null }],
  state: "not_ready",
  basis: {
    records: [
      {
        system: "crm",
        table: "discount_requests",
        id: "DR-9001",
        // The CRM's own columns, as read; §3.5 maps them to requested_discount 0.15 and so on.
        fields: {
          requested_discount_pct: "15.0",
          request_date: "2026-09-23",
          requested_by: "sarah.chen@northstar.example",
          product_sku: "NS-500",
        },
        read_at: "2026-09-23T10:02:00-05:00",
        last_changed: null,
      },
    ],
    documents: [
      { doc_id: "PRICING-POLICY-2026", sha256: "…", registered: true },
      { doc_id: "ACME-MFG-2025", sha256: "…", registered: true },
      { doc_id: "EXC-ACME-NS500-15", sha256: "…", registered: true },
    ],
  },
  register_used: [
    { doc_id: "PRICING-POLICY-2026", sha256: "…", status: "in_force", file_matches: true },
    { doc_id: "EXC-ACME-NS500-15", sha256: "…", status: "in_force", file_matches: true },
  ],
  floor: { subject: "DR-9001", level: 1, set_by: { decision_id: "DEC-0418", version: 1 }, confirmed_by: null },
  executed: [],
  previous: null,
};

/** Step 2: the agent's tool asks for 8% on version 1. The actor is the session's, not the body's. */
export const ask8: ClearanceRequest = {
  decision_id: "DEC-0418",
  decision_version: 1,
  action: "apply_discount",
  params: { ...params15, discount: 0.08 },
};

export const refused8: ClearanceResponse = {
  cleared: false,
  reasons: [
    { code: "differs", detail: "15% was decided; 8% was asked for." },
    { code: "condition_open", detail: "Confirm the discount on DR-9001.", waiting_on: [sarah], condition_id: "c1" },
    { code: "awaiting_approval", detail: "The VP Sales approves.", waiting_on: [michael] },
  ],
};

/** Steps 3–5: Sarah confirms the CRM and the decision re-runs. Version 2 as read after Michael's approval. */
export const v2AfterApproval: DecisionRecord = {
  ...v1,
  version: 2,
  decided_at: "2026-09-23T10:31:00-05:00",
  conditions: [
    {
      ...v1.conditions[0],
      resolved: { by: sarah, at: "2026-09-23T10:30:00-05:00", resolution: "confirmed_record", note: null, rerun_version: 2 },
    },
  ],
  approvals: [{ ...v1.approvals[0], given: { by: michael, at: "2026-09-23T11:40:00-05:00", note: null } }],
  state: "ready",
  previous: { version: 1, what_changed: "Sarah Chen confirmed the CRM's 15%; no conditions remain." },
};

/** Step 6. */
export const cleared15: ClearanceResponse = {
  cleared: true,
  clearance_id: "CLR-55120",
  bound: { decision_id: "DEC-0418", decision_version: 2, action: "apply_discount", params: params15, actor: dealDesk },
  expires_at: "2026-09-23T11:47:00-05:00",
  single_use: true,
};

/** Step 7: a replay. */
export const replay: RedeemResponse = {
  redeemed: false,
  reasons: [{ code: "used", detail: "CLR-55120 was redeemed at 11:42." }],
};

const executed: Execution = {
  action: "apply_discount",
  decision_id: "DEC-0418",
  version: 2,
  clearance_id: "CLR-55120",
  redeemed_at: "2026-09-23T11:42:00-05:00",
  report: "applied",
  incident_id: null,
};

/** Step 7: apply_discount is spent for DR-9001, so a new clearance on DEC-0418 is refused. */
export const afterSpent: ClearanceResponse = {
  cleared: false,
  reasons: [{ code: "spent", detail: "apply_discount on DR-9001 was executed by DEC-0418 under CLR-55120 at 11:42." }],
};

/**
 * Step 7: a later decision on DR-9001 can be made (DEC-0418 is no longer live),
 * but the action is spent for the subject, so it's spent from version 1.
 */
export const laterDecision: DecisionRecord = {
  ...v1,
  decision_id: "DEC-0431",
  requested_at: "2026-09-24T09:10:00-05:00",
  decided_at: "2026-09-24T09:10:01-05:00",
  // Asked with nothing submitted, so no input conflict: the CRM still says 15%.
  submitted: null,
  conditions: [],
  state: "spent",
  executed: [executed],
};

export const laterDecisionRefused: ClearanceResponse = {
  cleared: false,
  reasons: [{ code: "spent", detail: "apply_discount on DR-9001 was executed by DEC-0418 under CLR-55120 at 11:42." }],
};

/** A second decision on DR-9001 while DEC-0418 is live: DC-6, 409. */
export const secondDecision: Refusals = {
  refusals: [
    {
      rule: "DC-6",
      detail: "DR-9001 already has a live decision. Re-run it, or withdraw it first; its floor stays with DR-9001.",
      existing: "DEC-0418",
    },
  ],
};

/** The branch the ratchet closes: Sarah edits the CRM to 8% and resolves c1 as corrected. */
export const v2Ratchet: DecisionRecord = {
  ...v1,
  version: 2,
  decided_at: "2026-09-23T10:22:00-05:00",
  outcome: "APPROVE",
  gated_outcome: "APPROVE",
  findings: {
    type: "discount",
    commercial_eligibility: { status: "eligible", maximum_discount: 0.15, basis: "EXC-ACME-NS500-15" },
    authority: { policy: "PRICING-POLICY-2026", requestor_limit: 0.1, requestor_authorized: true, required_role: null, approver: null },
  },
  flags: [
    {
      code: "self_sourced_basis",
      text: "DR-9001 requested_discount changed from 0.15 to 0.08 by Sarah Chen at 10:21, after the request.",
      routes: false,
      about: ["DR-9001"],
    },
    { code: "ratchet", text: "Below DR-9001's floor: version 1 needed the VP Sales.", routes: false, about: ["DR-9001"] },
  ],
  conditions: [
    {
      ...v1.conditions[0],
      resolved: { by: sarah, at: "2026-09-23T10:22:00-05:00", resolution: "corrected_record", note: null, rerun_version: 2 },
    },
    {
      id: "c2",
      source: "ratchet",
      what: "Confirm the lower approval level: version 1 needed the VP Sales; version 2 is within Sarah Chen's own authority.",
      who: [michael],
      blocking: true,
      field: null,
      submitted: null,
      on_record: null,
      opened_in_version: 2,
      resolved: null,
    },
  ],
  approvals: [],
  actions: [{ action: "apply_discount", params: { ...params15, discount: 0.08 }, expected_actor: null }],
  state: "not_ready",
  floor: { subject: "DR-9001", level: 1, set_by: { decision_id: "DEC-0418", version: 1 }, confirmed_by: null },
  previous: { version: 1, what_changed: "The CRM now says 8%, changed by the requester; the level fell below the floor." },
};
