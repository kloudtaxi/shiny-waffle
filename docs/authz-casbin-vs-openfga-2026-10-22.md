# AuthZ for the prototype: Casbin or OpenFGA?

2026-10-22. The user asked for a review of Casbin (`apache/casbin`) as the prototype's AuthZ engine
before deciding, as the alternative to OpenFGA (embedded in Authorizer). Desk review only: docs via
Context7 and the web, plus sovera-owm's port contract (read-only). Nothing was installed or run.

**Short answer: keep OpenFGA, behind sovera-owm's `AuthorizationProvider` port. Keep Casbin as the
fallback adapter.** Our access questions are about relationships, and the approvals inbox needs a
reverse lookup. Those are what OpenFGA is built for. The OWM core team's adapter and the canon both
already use it, and the project is more mature. Casbin's strongest feature is conditions and
attributes inside the policy. That's the business authority we decided to keep in the OWM.

## 1. What the prototype asks of AuthZ

AuthZ answers access questions only. The OWM keeps business authority: approval bands, separation
of duties, the ratchet (decided 2026-10-22).

| # | Question | Example |
|---|---|---|
| Q1 | May this principal call this operation in this org? | May the Deal Desk agent call `decide`? May it call `approve`? |
| Q2 | Does this agent act for this person, under a mandate or delegation in force? | The agent acts for Sarah; the Approvals agent acts for Michael under D-17 |
| Q3 | Does this agent hold any approval grant for this use case? | The Approvals agent may approve `discount` at all (the OWM checks the limits) |
| Q4 | Which objects may this principal see or act on? | Michael's approvals inbox: the decisions waiting on him |
| Q5 | Is the principal in this org (the tenant)? | Every call |

Under a delegated token, the OWM checks both the actor (the agent) and the subject (the person).

## 2. Casbin in brief

- **What it is:** a policy-enforcement library, not a server. pycasbin runs in process, with
  `enforce`, `enforce_ex`, `batch_enforce` and an async enforcer. Policies live in a database
  through adapters (SQLAlchemy, so SQLite works), and watchers keep several processes in sync.
- **Its model is PERM:** a request definition, a policy definition, role definitions, an effect
  and a matcher expression. Models it supports out of the box:
  - ACL;
  - RBAC, including domains (multi-tenant), patterns, and conditions on role links (a link is
    valid only while a function returns true, such as a time window);
  - ABAC, where matchers read request attributes and call custom functions;
  - ReBAC, as roles per resource: `g, alice, doc1, collaborator` plus a resource type.
- **Explanations:** `enforce_ex` returns the policy row that matched, so a record can say which
  rule allowed a call.
- **Reverse lookup:** `get_implicit_permissions_for_user` lists a user's policies, including
  inherited roles. There is no general "which objects" query when the matcher uses attributes.
- **Governance:** an Apache Incubator podling since 2026-02-07. Its first ASF release candidate got
  a binding −1 in August (signing, checksums, licence headers). The second passed, according to the
  September report, which is still a draft. The IPMC raised IP-clearance follow-ups and the size of
  the project (249 repositories), and noted in May that development still happens mostly outside ASF
  infrastructure. It hasn't graduated.

## 3. OpenFGA (in Authorizer) in brief

- **What it is:** Zanzibar-style ReBAC. A model in a DSL defines types and relations, and access is
  granted by writing relationship tuples.
  - Relations compose: `viewer from parent`, group usersets, exclusions (`but not`).
  - `check` asks whether a relation holds, and `list_objects` answers the reverse question from an
    index.
  - OpenFGA itself supports CEL conditions and contextual tuples.
- **In Authorizer:** it is embedded and exposed as `/v1/check_permissions` (1–100 checks).
  - The subject comes from the caller's token; only a super-admin, or the subject itself, may name
    another subject.
  - Conditions can't be used through Authorizer's API. Contextual tuples or scheduled tuple deletion
    stand in for them.
- **Governance:** a CNCF Incubating project since 2025-10-28, after Sandbox in 2022.
- **At BlueLeaf:** the canon names OPA and OpenFGA for agent authority (v1.2). sovera-owm's
  `AuthorizationProvider` port (`check`, `list_objects`, fail closed, unauthorized = absence) has an
  `OpenFGAAuthorizationAdapter`.

## 4. Side by side, on our questions

| | Casbin (pycasbin, in process) | OpenFGA (in Authorizer) |
|---|---|---|
| Q1 operation access | Good: RBAC with domains | Good: a relation per operation |
| Q2 acts-for and delegation | Workable: a role link, or the actor in the request. Chains of delegation are awkward | Natural: `agent#acts_for@user`, and chains compose |
| Q3 agent grant exists | Good | Good |
| Q4 inbox (reverse lookup) | Only by listing implicit permissions; none for attribute matchers | Native: `list_objects` |
| Q5 tenant | RBAC domains | An `org` type, with relations scoped to it |
| Actor and subject checked separately | Easy: both go in the request | Two checks. Through Authorizer this needs the super-admin path or contextual tuples (spike item 1) |
| Says which rule allowed a call | `enforce_ex` returns the row | `check` returns only allowed; `expand` shows the tree |
| Conditions and limits in AuthZ | Strong (ABAC, link conditions). This is the part we decided to keep in the OWM | Not through Authorizer; in OpenFGA as CEL |
| Deployment | A library in the OWM process; policy kept in SQLite | One service shared for AuthN and AuthZ (Authorizer, SQLite) |
| Consistency across processes | Watchers; eventual | One store; Zanzibar consistency |
| sovera-owm port fit | `check` fits `enforce`. `list_objects` fits for RBAC only | Fits both methods; the adapter exists |
| Re-cut cost | A new adapter in sovera-owm, and a canon amendment | Swap Authorizer's adapter for theirs |
| Maturity | ASF podling with release and IP issues still being worked | CNCF Incubating |
| Policy as data | Rows. The model file and matchers are code-like expressions (SimpleEval; `eval()` in matchers is possible) | Tuples. The model is a declarative DSL |

## 5. Where each wins

**Casbin wins when:**
- you want AuthZ in process with no service to run;
- most rules are attribute-based (amounts, times, tiers) and live in AuthZ;
- each allowed call should record the rule that allowed it.

**OpenFGA wins when:**
- the questions are relationships (acts-for, member-of, owns, approver-on) that compose;
- you need "list what this principal can act on" (the inbox);
- one AuthZ model has to serve several services and runtimes consistently;
- it has to match what the OWM team already runs.

The prototype is in the second case. The first case is Casbin's sweet spot, and it overlaps the
business authority the OWM keeps on purpose: grants with limits, windows and caps. Putting that in
Casbin would split authority across two engines and take the reasons out of the decision record.

## 6. Recommendation and fallbacks

1. **OpenFGA through Authorizer**, behind sovera-owm's port, with the model kept in `contract/`.
2. **If the spike shows the actor-and-subject check needs Authorizer's super-admin path,** run
   OpenFGA's own server beside Authorizer for checks. The core team's adapter already talks to
   OpenFGA's API, where any subject can be named. Authorizer then keeps AuthN and delegation.
3. **Casbin as the fallback adapter** behind the same port, if a service is unwelcome or OpenFGA
   fails the spike. That costs:
   - a new adapter for the OWM team;
   - an amendment to the canon's v1.2 choice;
   - an inbox built by listing implicit permissions rather than a reverse index.

**If you choose Casbin anyway:** use an RBAC-with-domains model and keep matchers free of
attributes, so the OWM stays the only place limits live. Put the actor in the request
(`r = sub, actor, dom, obj, act`). Back it with the SQLAlchemy adapter on SQLite. Pin a release,
because the ASF release process is still settling.

## Sources

- Casbin docs via Context7 (`/apache/casbin-pycasbin`, `/websites/casbin`): `enforce_ex`, filtered
  loading, RBAC with domains and conditions, ABAC, ReBAC, implicit permissions.
- Apache Incubator: [Casbin podling status](https://incubator.apache.org/clutch/casbin.html),
  [July 2026 report](https://cwiki.apache.org/confluence/spaces/INCUBATOR/pages/435028221/July2026),
  [August 2026](https://cwiki.apache.org/confluence/spaces/INCUBATOR/pages/446070925/August2026),
  [September 2026 draft](https://cwiki.apache.org/confluence/spaces/INCUBATOR/pages/449282805/September2026),
  [May 2026](https://cwiki.apache.org/confluence/spaces/INCUBATOR/pages/421957153/May2026).
- OpenFGA: [project page](https://openfga.dev/project),
  [CNCF incubation announcement](https://www.cncf.io/blog/2025/11/11/openfga-becomes-a-cncf-incubating-project/).
- Authorizer docs via Context7 (`/websites/authorizer_dev`): `/v1/check_permissions`, the
  authorization model, token exchange.
- sovera-owm `specs/001-identity-authz-ports/contracts/authorization-provider.md` (read-only).
