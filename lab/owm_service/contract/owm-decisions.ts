/**
 * The v1.2 contract on `owm-decisions`: the shapes the OWM service serves for
 * the register, decisions, approvals and clearance. owm/docs/contract-v1.2.md
 * is the reference; section numbers below point into it. Revised after the
 * lab's review and re-review (shiny-waffle docs/contract-v1.2-review-2026-10-09.md,
 * c196b31 and 74aef92).
 *
 * Nothing imports this yet. web-next moves onto it in B-07, and the lab builds
 * its OWM service to it.
 */

/* ---------------------------------------------------------------- §3 common */

/** An employee, from the HR export. */
export interface PersonRef {
  id: string;
  name: string;
  title: string;
  function: string;
}

/** Who acted (phase 0). Always the session's, `on_behalf_of` included; never taken from a body (§3.3). */
export type Actor =
  | { kind: "person"; person: PersonRef }
  | {
      kind: "agent";
      id: string;
      name: string;
      /** sha256 of what runs: instructions, tools, model. */
      version: string;
      /** null for a service principal, which acts for its owning function. */
      on_behalf_of: PersonRef | null;
      mandate: { doc_id: string } | null;
    };

/** GET /me: the session's actor as the OWM knows it, with their function from HR (§3.3). */
export interface MeResponse {
  actor: Actor;
}

/** A bootstrap entry may name a function, where the HR export has nobody (base.yaml). */
export type Party = PersonRef | { kind: "function"; function: string; note: string };

export type RegisterRule =
  | "RR-1" | "RR-2" | "RR-3" | "RR-4" | "RR-5" | "RR-6" | "RR-7"
  | "RR-8" | "RR-9" | "RR-10" | "RR-11" | "RR-12" | "RR-13" | "RR-14";
export type DecisionRule = "DC-1" | "DC-2" | "DC-3" | "DC-4" | "DC-5" | "DC-6";
export type RuleCode = RegisterRule | "ADM" | DecisionRule;

export interface Refusal {
  rule: RuleCode;
  /** Plain words: what failed and what would fix it. */
  detail: string;
  /** RR-6, RR-7: the term or phrase the text doesn't state (G-44). */
  unmatched?: string;
  /** RR-10: the supersession to offer the submitter. Never applied silently (G-44). */
  fix?: { relations: { type: "supersedes"; target: string }[] };
  /** DC-6: the live decision on this subject. */
  existing?: string;
}

/** The body of a 422 (and of a 403 or 409 that names a rule). */
export interface Refusals {
  refusals: Refusal[];
}

/**
 * §3.5: one name per figure, the truth model's (the oracle compares by these).
 * The service converts from each system's column, e.g. the CRM's
 * requested_discount_pct "15.0" is requested_discount 0.15.
 */
export type SubmittedField =
  | "requested_discount"
  | "requested_limit_usd"
  | "current_limit_usd"
  | "request_date"
  | "status"
  | "customer"
  | "product"
  | "requestor";

export type Submitted = Partial<Record<SubmittedField, string | number>>;

/* -------------------------------------------------------------- §4 register */

/** Northstar's kinds (registrar.py OWNER), plus procedure and agent_mandate. */
export type KnownDocKind =
  | "pricing_policy" | "agreement" | "amendment" | "exception"
  | "credit_policy" | "guarantee"
  | "sla_schedule" | "support_terms" | "severity_guide" | "escalation_procedure" | "holiday_calendar"
  | "procedure"
  /** Held (§9): only the bootstrap import has these in v1.2. */
  | "agent_mandate";

/**
 * Kinds and their owners are the organisation's configuration (the registrar's
 * OWNER map), so another organisation may add its own. RR-5 still refuses a
 * kind the organisation hasn't configured (§4.4).
 */
export type DocKind = KnownDocKind | (string & {});

export type Relation = { type: "supersedes" | "under"; target: string };

export type EntryStatus = "scheduled" | "in_force" | "superseded" | "expired" | "revoked";

export interface RegisterEntry {
  doc_id: string;
  kind: DocKind;
  title: string;
  owning_function: string;
  /** "company", or a customer (and product, guarantor). */
  scope: string;
  /** Of the approved text, computed by the service (RR-5). */
  sha256: string;
  effective_from: string;
  effective_to: string | null;
  relations: Relation[];
  terms: Record<string, unknown>;
  proposed_by: Actor | null;
  registered_by: Party;
  approved_by: Party;
  registered_on: string;
  approved_on: string;
  revoked: { on: string; by: PersonRef; approved_by: PersonRef } | null;
  /** As of the read. */
  status: EntryStatus;
  superseded_by: string | null;
  /**
   * The copy on file, checked against the registered sha256. source_id is the
   * knowledge foundation's id for that copy, so a source page can find its
   * register entry (§4.1).
   */
  file: { sha256: string; matches: boolean; detail: string | null; source_id: string | null };
}

/** Entries that supersede one another, shown as one document's versions. A view, not stored. */
export interface RegisterSeries {
  series_id: string;
  kind: DocKind;
  scope: string;
  title: string;
  /** doc_ids, oldest first. */
  entries: string[];
  in_force: string | null;
}

export interface Coverage {
  decision_type: string;
  label: string;
  procedure: { id: string; version: number } | null;
  documents: { doc_id: string; title: string }[];
  /** Set when nothing governs this kind of decision: what happens instead (G-31). */
  gap: string | null;
}

export type MismatchMode = "use_registered" | "route";

/** GET /register?as_of= */
export interface RegisterView {
  /** The register's change counter, which RR-13 compares. */
  version: number;
  clock: string;
  entries: RegisterEntry[];
  series: RegisterSeries[];
  coverage: Coverage[];
  settings: { on_mismatch: MismatchMode };
}

export type ChangeState = "draft" | "pending" | "approved" | "declined" | "withdrawn" | "refused";

export interface RegisterChange {
  change_id: string;
  action: "register" | "revoke";
  state: ChangeState;
  base_version: number;
  doc_id?: string;
  kind?: DocKind;
  title?: string;
  sha256?: string;
  effective_from?: string;
  effective_to?: string | null;
  terms?: Record<string, unknown>;
  relations?: Relation[];
  target?: string;
  revoked_on?: string;
  proposed_by: Actor | null;
  /** When the draft was made (B-11). null for a change submitted directly. */
  proposed_at: string | null;
  submitted_by: PersonRef | null;
  submitted_at: string | null;
  /** RR-4: the owning function's head and the Executives, never the submitter. */
  approvers: PersonRef[];
  approved_by: PersonRef | null;
  approved_at: string | null;
  declined: { by: PersonRef; at: string; note: string } | null;
  /** Set when approval found a rule broken. */
  refused: Refusal[] | null;
  /** Against the entry it supersedes, for the reviewer (G-33). */
  diff: { key: string; label: string; was: string | null; now: string | null }[];
  /** Drafts only: what the rules would refuse on submit. */
  checks?: Refusal[];
}

/** POST /register/changes */
export type RegisterChangeRequest = (
  | {
      action: "register";
      doc_id: string;
      kind: DocKind;
      title: string;
      /** The full text. The service computes the fingerprint (RR-5). */
      text: string;
      effective_from: string;
      effective_to: string | null;
      terms: Record<string, unknown>;
      relations: Relation[];
    }
  | { action: "revoke"; target: string; revoked_on: string }
) & {
  base_version: number;
  /** false: a draft, which anyone may make, agents included. */
  submit: boolean;
  proposed_by?: Actor;
  /** The session's. A copy that differs is refused with RR-1 (§3.3). */
  submitted_by?: string;
};

/* ------------------------------------------------------------- §5 decisions */

export type DecisionType = "discount" | "credit" | "sla";

export type ApprovalOutcome =
  | "APPROVE"
  | "APPROVE_WITH_AUTHORIZATION"
  | "REJECT_OR_ESCALATE"
  | "REVIEW_REQUIRED"
  | "REQUEST_EVIDENCE";

export type SlaOutcome = "BREACH_CREDIT_OWED" | "BREACH_NO_CREDIT" | "NO_BREACH" | "OUT_OF_SCOPE" | "CANNOT_DECIDE";

export type Outcome = ApprovalOutcome | SlaOutcome;

/** Each type's route_to: what a route stands as. There is no ROUTED outcome. */
export const ROUTE_TO: Record<DecisionType, Outcome> = {
  discount: "REQUEST_EVIDENCE",
  credit: "REQUEST_EVIDENCE",
  sla: "CANNOT_DECIDE",
};

export interface Authority {
  policy: string | null;
  /** A fraction (discount) or USD (credit). */
  requestor_limit: number | null;
  requestor_authorized: boolean | null;
  required_role: string | null;
  approver: PersonRef | null;
}

export interface DiscountFindings {
  type: "discount";
  commercial_eligibility: {
    status: "eligible" | "exceeded" | "not_covered" | "unknown" | "standard";
    maximum_discount: number | null;
    basis: string | null;
  };
  authority: Authority | null;
}

export interface CreditFindings {
  type: "credit";
  eligibility: {
    status: "eligible" | "exceeded" | "ineligible" | "unknown";
    maximum_limit_usd: number | null;
    basis: string | null;
  };
  authority: Authority | null;
  /** The registered terms it read, e.g. "CREDIT-POLICY-2026 v1". */
  registered: string[];
}

export interface Obligation {
  party: "organization" | "counterparty";
  duty: "engage" | "notify" | "decide_claim" | "issue_memo" | "record_root_cause" | "phone_report" | "claim";
  role: string | null;
  /** null when nobody, or more than one person, holds the role. */
  holder: PersonRef | null;
  /** A holder the kernel defers, e.g. "owner:CRM-2048". */
  holder_ref: string | null;
  due: string | null;
  /** Counterparty duties only. */
  status: "met" | "not_met" | null;
}

export interface SlaFindings {
  type: "sla";
  scope: "in" | "out" | null;
  severity: 1 | 2 | 3 | 4 | null;
  breach: {
    response: "met" | "missed" | "not_applicable" | "cannot_decide";
    restoration: "met" | "missed" | "missed_band1" | "missed_band2" | "not_applicable" | "cannot_decide";
  } | null;
  credit_usd: number | null;
  obligations: Obligation[];
  account_owner: PersonRef | null;
}

export type Findings = DiscountFindings | CreditFindings | SlaFindings;

/** A narrow judgment, as the kernel's `judge` records it (§5.4). */
export type Judgment =
  | {
      q: string;
      /** The document or record it was about. null until the kernel records it (§12.4). */
      about: string | null;
      form: "choice";
      choice: string;
      probabilities: Record<string, number>;
      /** Uncertain below 0.5 (CHOICE_FLOOR). */
      confidence: number;
      uncertain: boolean;
    }
  | {
      q: string;
      about: string | null;
      form: "yes_no";
      yes: boolean;
      /** The kernel's `noul`. Uncertain from 0.30 to 0.70 (NOUL_BAND). */
      p_yes: number;
      uncertain: boolean;
    };

export type FlagCode =
  | "routed"
  | "withheld"
  | "incident"
  | "conflict"
  | "tamper"
  | "mismatch"
  | "set_aside"
  | "not_on_file"
  | "revoked"
  | "self_sourced_basis"
  | "ratchet"
  | "cannot_decide"
  | "out_of_scope"
  | "note"
  /** Reserved: not emitted until the truth has a duplicate-request scenario and the lab has tested it (§12.3). */
  | "possible_duplicate";

export interface Flag {
  code: FlagCode;
  /** The kernel's string, or the service's own. */
  text: string;
  /** Did this flag send the decision to route_to? */
  routes: boolean;
  /** doc_ids or record ids it names. */
  about: string[];
  /** possible_duplicate: the other request's decision and its floor, shown to the approver. */
  related?: { subject: string; decision_id: string; floor: number | null };
}

export type ConditionSource = "input_conflict" | "missing_record" | "ratchet";
export type Resolution = "confirmed_record" | "corrected_record" | "confirmed_lower_level";

export interface Condition {
  /** Unique within the decision, across versions. */
  id: string;
  source: ConditionSource;
  what: string;
  /** Any one of them may resolve it. */
  who: PersonRef[];
  blocking: boolean;
  /** input_conflict: the figure that differs (§3.5). */
  field: SubmittedField | null;
  submitted: unknown;
  on_record: unknown;
  opened_in_version: number;
  resolved: {
    by: PersonRef;
    at: string;
    resolution: Resolution;
    note: string | null;
    rerun_version: number;
  } | null;
}

export interface ApprovalRequirement {
  kind: "approval" | "concurrence" | "claim_decision";
  /** The HR title the policy names. */
  role: string;
  person: PersonRef | null;
  passed_from: { person: PersonRef; reason: "separation_of_duties" } | null;
  given: { by: PersonRef; at: string; note: string | null } | null;
  declined: { by: PersonRef; at: string; note: string } | null;
}

export type ActionName = "apply_discount" | "set_credit_limit" | "issue_service_credit";

export interface DecidedAction {
  action: ActionName;
  params: Record<string, unknown>;
  /** Who the decision expects to act, e.g. S36's issue_memo holder. Shown, not enforced in v1.2. */
  expected_actor: PersonRef | null;
}

/** What the decision rested on. A change to any of it makes the decision stale for clearance. */
export interface Basis {
  records: {
    system: string;
    table: string;
    id: string;
    /** Only the fields the decision relied on, so unrelated changes don't make it stale. */
    fields: Record<string, unknown>;
    read_at: string;
    /** From the system of record's change history, where it has one (§12.8). */
    last_changed: { by: PersonRef | null; at: string } | null;
  }[];
  documents: { doc_id: string; sha256: string; registered: boolean }[];
}

/**
 * Live unless withdrawn, declined or spent. One live decision per subject (DC-6).
 * spent: every action it decided was already executed on its subject, by this
 * decision or another (§5.9).
 */
export type DecisionState =
  | "no_action"
  | "not_ready"
  | "awaiting_approval"
  | "declined"
  | "ready"
  | "spent"
  | "withdrawn";

export interface DecisionRecord {
  decision_id: string;
  /** 1, then +1 on every re-run (§6). */
  version: number;
  decision_type: DecisionType;
  subject: { request_id?: string; ticket?: string; account_id?: string; customer_id?: string; product?: string };
  /** Figures as submitted: compared with the record, never used (§3.5 names). */
  submitted: Submitted | null;
  /** From the system of record's row. null for SLA tickets. */
  requested_by: PersonRef | null;
  /** Who asked, from the session. */
  actor: Actor;
  requested_at: string;
  /**
   * The date the policy in force is read for: the record's request_date
   * (discount, credit) or the service clock (SLA). Never from the body (S23's
   * trap), and a re-run doesn't move it.
   */
  as_of: string;
  decided_at: string;
  decided_by: {
    kind: "owm";
    procedure: { id: string; version: number; sha256: string };
    judgments: number;
    uncertain: number;
  };
  /** The rules' outcome. null when withheld (G-32). */
  outcome: Outcome | null;
  /** What stands, after the gate. */
  gated_outcome: Outcome;
  routed: boolean;
  findings: Findings;
  judgments: Judgment[];
  flags: Flag[];
  conditions: Condition[];
  approvals: ApprovalRequirement[];
  actions: DecidedAction[];
  state: DecisionState;
  basis: Basis;
  register_used: { doc_id: string; sha256: string; status: "in_force" | "revoked"; file_matches: boolean }[];
  /** The ratchet (G-46): the subject's floor, not the decision's. null for SLA. */
  floor: {
    subject: string;
    level: number;
    set_by: { decision_id: string; version: number };
    confirmed_by: PersonRef | null;
  } | null;
  /** Actions executed on this subject, by any decision. An action runs once per subject (§5.9). */
  executed: Execution[];
  previous: { version: number; what_changed: string } | null;
}

/** One execution of an action on a subject. Spent at redemption, whatever the report says. */
export interface Execution {
  action: ActionName;
  decision_id: string;
  version: number;
  clearance_id: string;
  redeemed_at: string;
  report: "applied" | "failed" | null;
  /** Raised by a failed report. The action stays spent (fail-closed). */
  incident_id: string | null;
}

/**
 * POST /decisions. Only the subject's id is named; everything else, as_of and
 * requested_by included, is read from its row. There is deliberately no as_of.
 */
export interface DecisionRequest {
  decision_type: DecisionType;
  subject: { request_id: string } | { ticket: string };
  submitted?: Submitted;
}

/** POST /decisions/{id}/conditions/{cid}/resolve. Never carries a value: the OWM reads the record. */
export interface ResolveRequest {
  decision_version: number;
  resolution: Resolution;
  note?: string;
}

export interface DecisionEvent {
  at: string;
  actor: Actor;
  version: number;
  kind:
    | "requested"
    | "decided"
    | "condition_resolved"
    | "rerun"
    | "approved"
    | "declined"
    | "withdrawn"
    | "clearance_cleared"
    | "clearance_refused"
    | "clearance_redeemed"
    | "execution_reported"
    | "incident_raised";
  detail: string;
}

/* ------------------------------------------------------------- §7 clearance */

/** In the order they're checked. Every failing check is returned. */
export type ClearanceCode =
  /** Version not current, basis changed, or a register_used document revoked by the action date. */
  | "stale"
  /** The action was already executed on this subject, by this decision or another (§5.9). */
  | "spent"
  | "suspended"
  /** Also a mandate's limits, named in the detail. */
  | "outside_mandate"
  | "differs"
  | "condition_open"
  | "awaiting_approval"
  | "declined";

export interface ClearanceRequest {
  /** Must equal the path's (422 otherwise). */
  decision_id: string;
  decision_version: number;
  action: ActionName;
  params: Record<string, unknown>;
  /** The session's. A copy that differs is refused with RR-1 (§3.3). */
  actor?: Actor;
  /** Check and log; issue nothing. The UI's "Try to act". */
  dry_run?: boolean;
}

export interface ClearanceReason {
  code: ClearanceCode;
  detail: string;
  waiting_on?: PersonRef[];
  condition_id?: string;
}

export type ClearanceResponse =
  | {
      cleared: true;
      clearance_id: string;
      bound: {
        decision_id: string;
        decision_version: number;
        action: ActionName;
        params: Record<string, unknown>;
        actor: Actor;
      };
      expires_at: string;
      single_use: true;
    }
  | { cleared: false; reasons: ClearanceReason[] }
  /** v1.3 (R34): a dry run's only response. `reasons` is empty exactly when `would_clear`. */
  | { dry_run: true; would_clear: boolean; reasons: ClearanceReason[] };

/**
 * POST /clearances/{id}/redeem, by the adapter that holds the system's credential. v1.3 (R58): any
 * authenticated actor may redeem; only the actor who redeemed may report.
 */
export interface RedeemRequest {
  params: Record<string, unknown>;
  executor: { system: string; adapter: string };
}

export type RedeemResponse =
  | { redeemed: true; at: string }
  | {
      redeemed: false;
      reasons: {
        code: "used" | "expired" | "mismatch" | "stale" | "spent" | "condition_open" | "suspended";
        detail: string;
      }[];
    };

/** POST /clearances/{id}/report. A failed execution stays spent and raises an incident. */
export interface ReportRequest {
  status: "applied" | "failed";
  external_ref: string | null;
  detail: string | null;
}

export interface ReportResponse {
  /** Set when status is failed. */
  incident_id: string | null;
}

export interface ClearanceAttempt {
  at: string;
  /** From the session. */
  actor: Actor;
  request: ClearanceRequest;
  response: ClearanceResponse;
}

/* ------------------------------------------------------------- §8 approvals */

export interface WorkItem {
  /** register_draft (B-11): an agent's draft, for anyone in the owning function to submit or dismiss. */
  kind: "register_change" | "register_draft" | "decision_approval" | "condition";
  id: string;
  title: string;
  detail: string;
  raised_by: Actor;
  raised_at: string;
  waiting_on: PersonRef[];
  /** decision_approval only: the open blocking conditions holding it (DC-4). */
  held_by: { condition_id: string; what: string; who: PersonRef[] }[];
  /** v1.3: the OWM resource (e.g. /api/v1/decisions/DEC-0001). Map it to a page with `workItemHref`. */
  href: string;
}

/** GET /approvals */
export interface ApprovalsView {
  waiting_on_you: WorkItem[];
  waiting_on_others: WorkItem[];
  done: (WorkItem & { result: string; at: string })[];
}

/* ---------------------------------------------------------------- §9 agents */

/**
 * The terms of an agent_mandate entry. Bootstrap only in v1.2. When mandates are
 * registrable, the owner comes from owner.function, not from the kind.
 */
export interface AgentMandateTerms {
  agent: { id: string; name: string; purpose: string; runtime: "agno" | "external" };
  owner: { function: string; accountable: PersonRef };
  /** delegated: one per team, acting for whoever asks. */
  principal: "delegated" | "service";
  team: string | null;
  /** The versions (sha256) allowed to run under it. */
  versions: string[];
  may_ask: { decision_type: DecisionType; scope: string }[];
  may_do: {
    action: ActionName;
    decision_types: DecisionType[];
    /** Per param. Anything not listed is exact. */
    match: Record<string, "exact" | "at_most">;
    /** e.g. { per_day: 200 }. Passing one is refused as outside_mandate. */
    limits: Record<string, number> | null;
  }[];
  may_propose: ("register_change" | "procedure" | "identity_merge")[];
}
