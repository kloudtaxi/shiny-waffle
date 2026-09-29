## Sovera OWM PRD 3
Sep 29, 2026

# **Sovera OWM**

## **Product Requirements Document**

### **Superseding PRD — Organizational Understanding & Decision Substrate**

**Status:** Supersedes previous OWM PRD
**Product:** Sovera OWM
**Version:** 2.0
**Date:** September 2026

---

# **1. Executive Summary**

Enterprise AI has become increasingly capable of retrieving information, reasoning over documents, querying databases, and executing workflows.

The remaining problem is organizational understanding.

An enterprise does not operate as a collection of documents and database rows. It operates through entities, relationships, authority, policies, exceptions, procedures, temporal state, and decisions.

AI can reconstruct much of this understanding from enterprise evidence at inference time. But reconstruction is not the same thing as having an organizational model.

**Sovera OWM — Organizational World Model — is the persistent, governed representation of how an organization works.**

OWM sits between the enterprise’s knowledge foundation and its AI agents.

```
ENTERPRISE EVIDENCE
                           │
                           ▼
                  KNOWLEDGE FOUNDATION
             identity / provenance / retrieval
                           │
                           ▼
              ┌──────────────────────────┐
              │           OWM            │
              │                          │
              │  DOMAIN MODEL            │
              │  ONTOLOGY                │
              │  ORGANIZATIONAL STATE    │
              │  POLICIES                │
              │  AUTHORITY               │
              │  PROCEDURES              │
              │  EXCEPTIONS              │
              │  CONSTRAINTS             │
              │  DECISIONS               │
              │                          │
              └────────────┬─────────────┘
                           │
                           ▼
                         AGENTS
                           │
                           ▼
                  ACTIONS / DECISIONS
```

The central product thesis is:

**AI can retrieve enterprise knowledge and reason over it. What it doesn’t inherently have is a persistent, governed model of how the organization works.**

OWM turns organizational evidence into persistent organizational understanding that AI can continuously reuse, validate, govern, and build upon.

---

# **2. Product Thesis**

## **2.1 The Problem**

Traditional enterprise AI architectures primarily optimize for access to information.

They answer questions such as:

* What does the contract say?
* What was the customer’s last order?
* What does the pricing policy say?
* Who is Sarah Chen?
* What is the current revenue?
But enterprise decisions require the system to understand how those facts relate.

For example:

Can Sarah approve a 15% discount for Acme on an NS-500?

Answering that question requires understanding:

* which customer is Acme;
* which CRM and ERP records refer to the same customer;
* which product is being requested;
* which contract applies;
* whether the contract is currently active;
* whether an exception applies;
* which pricing policy is effective on the request date;
* who requested the discount;
* what authority that person has;
* whether the requested discount falls within that authority;
* who must approve it;
* whether organizational constraints are satisfied;
* and what happened when the organization made similar decisions previously.
The required capability is not simply retrieval.

It is **organizational understanding**.

---

# **3. Product Definition**

## **3.1 What OWM Is**

OWM is a persistent organizational model that represents:

1. **What things mean within an organization**
2. **What is true about the organization**
3. **What rules govern the organization**
4. **Who has authority to act**
5. **How organizational decisions are made**
6. **What constraints relationships must satisfy**
7. **What decisions the organization has previously made**

⠀
OWM is continuously grounded in enterprise evidence and maintains provenance back to that evidence.

---

## **3.2 What OWM Is Not**

OWM is explicitly **not**:

* a generic RAG system;
* a document search engine;
* a vector database;
* a knowledge graph alone;
* a replacement for enterprise databases;
* an enterprise data warehouse;
* a generalized agent runtime;
* an LLM;
* an autonomous decision-maker;
* a workflow orchestration engine.
OWM may use these technologies, integrate with them, or expose capabilities to them.

But its product responsibility is different:

**OWM maintains the organizational model that allows agents to operate with organizational context.**

---

# **4. Product Boundary**

The platform should be deliberately componentized.

```
Enterprise Systems
       │
       ▼
┌───────────────────────┐
│ Knowledge Foundation  │
│                       │
│ Retrieval             │
│ Extraction            │
│ Identity              │
│ Provenance            │
│ Evidence              │
└───────────┬───────────┘
            │
            ▼
┌─────────────────────────────┐
│             OWM             │
│                             │
│ Domain Model                │
│ Ontology                    │
│ Organizational State        │
│ Policy & Authority          │
│ Procedures                  │
│ Constraints                 │
│ Decision Memory             │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│         Agent Runtime       │
│                             │
│ Agno / Other Runtime        │
│ Identity                    │
│ Tools                       │
│ Memory                      │
│ Execution                   │
└─────────────┬───────────────┘
              │
              ▼
        Actions / Decisions
```

Sovera owns the OWM layer.

The agent runtime is an implementation dependency, not the product category.

The knowledge foundation is an upstream capability, not the OWM itself.

---

# **5. Core OWM Primitives**

OWM should be organized around six primitives.

## **5.1 Domain Model**

Defines what entities and concepts mean within the organization.

Examples:

* Customer
* Account
* Employee
* Product
* Contract
* Order
* Department
* Role
* Territory
The domain model provides organizational semantics rather than merely generic entity types.

---

## **5.2 Organizational State**

Represents what is true about the organization at a point in time.

Examples:

* Acme is an active customer.
* Sarah owns Acme.
* Acme’s MSA is active.
* The NS-500 exception is valid.
* Michael is VP Sales.
* The 2026 pricing policy is effective.
State must be temporal.

OWM must distinguish:

```
What is true now?
What was true then?
When did it become true?
When did it stop being true?
What evidence established it?
```

---

## **5.3 Policy & Authority**

Represents organizational rules and authorization.

Examples:

```
Enterprise AE
    ≤ 10% discount

VP Sales
    >10% and ≤20%

CRO
    >20%
```

Authority is separate from policy eligibility.

A contract may permit a 15% discount while the requestor may not have authority to approve it.

OWM must preserve this distinction.

---

## **5.4 Procedures**

Procedures describe how an organization converts organizational state into decisions.

Example:

```
Discount Approval

1. Identify request
2. Resolve customer
3. Resolve product
4. Establish active contract
5. Establish applicable exception
6. Establish applicable policy
7. Establish requestor authority
8. Determine required approver
9. Make decision
10. Record decision
```

Procedures are a core OWM primitive.

They represent **how the organization works**, not simply what information it possesses.

---

## **5.5 Constraints**

Constraints represent organizational invariants and relationships that should remain valid.

Example:

```
reports_to:
  acyclic: true
  exactly_one_manager: true
  manager_role_rank: ">= subordinate_role_rank"
```

Constraints allow OWM to identify organizational contradictions instead of silently repairing them.

Example:

```
Evidence:
Michael Torres → reports_to → Sarah Chen

OWM:
CONFLICT DETECTED

Evidence contradicts organizational constraint.

Status:
REQUIRES_REVIEW
```

OWM should not silently overwrite or “fix” evidence because a different interpretation appears more plausible.

---

## **5.6 Decision Memory**

Decisions become part of organizational memory.

A decision should capture:

* decision ID;
* subject;
* decision;
* decision date;
* effective period;
* decision maker;
* authority used;
* relevant organizational state;
* procedure used;
* evidence;
* reasoning;
* exceptions;
* confidence;
* provenance.
Example:

```
decision:
  id: DEC-2026-0091
  request: DR-9001
  outcome: APPROVE_WITH_AUTHORIZATION
  approver: Michael Torres
  reason:
    - Acme MSA active
    - NS-500 exception permits 15%
    - Sarah Chen lacks authority for 15% under 2026 policy
    - VP Sales authority covers 15%
```

Decision memory allows future agents to reason from organizational history without reconstructing every prior decision from raw evidence.

---

# **6. Evidence and Provenance**

Evidence remains foundational.

OWM does not replace enterprise evidence.

Every organizational fact, state transition, policy, authority relationship, constraint, and decision should be traceable to supporting evidence where applicable.

Evidence may originate from:

* CRM;
* ERP;
* databases;
* SaaS systems;
* documents;
* email;
* contracts;
* spreadsheets;
* APIs;
* event streams;
* human input;
* previous decisions.
OWM should maintain provenance:

```
OWM Fact
   │
   ├── Source
   ├── Source Record
   ├── Source Timestamp
   ├── Extraction / Inference
   ├── Confidence
   └── Validity Period
```

The model must distinguish:

**Evidence**

from

**Organizational interpretation**

from

**Organizational decision**.

---

# **7. Identity Resolution**

Identity is a first-class OWM capability.

The same real-world entity may appear differently across enterprise systems.

Example:

```
Customer:
  canonical_id: CUST-1001

  identities:
    - system: CRM
      id: CRM-2048

    - system: ERP
      id: C-1001

    - system: Contract
      id: ACME-MFG-2025
```

OWM must preserve both:

* canonical organizational identity;
* source-system identity.
Canonicalization must never destroy source identifiers.

Agents should be able to ask:

Show me everything the organization knows about CUST-1001.

and:

What records across the enterprise correspond to CRM-2048?

---

# **8. Temporal Understanding**

Organizational truth changes over time.

OWM must support temporal validity for:

* policies;
* contracts;
* pricing;
* organizational roles;
* authority;
* relationships;
* exceptions;
* customer status;
* decisions.
Example:

```
2025 Policy
AE ≤ 15%

2026 Policy
AE ≤ 10%
VP Sales >10% and ≤20%
CRO >20%
```

The same request can therefore produce different organizational decisions depending on the request date.

OWM must answer:

What was true when this decision was made?

as well as:

What is true now?

---

# **9. Organizational Constraints**

OWM should support explicit organizational invariants.

Examples:

### **Hierarchy**

* reporting relationships must be acyclic;
* employees normally have one active manager;
* managers must have appropriate organizational rank.
### **Authority**

* approval authority must belong to an active role;
* authority must be valid for the decision date;
* delegated authority must have a valid delegation period.
### **Contracts**

* contract validity must respect effective dates;
* exceptions must reference applicable contracts/customers/products;
* expired agreements cannot authorize current decisions.
### **Decisions**

* decisions must identify the authority under which they were made;
* decisions must preserve the organizational state used at decision time.
Constraints should produce explicit conflicts rather than silent correction.

---

# **10. Organizational Procedures**

Procedures are executable descriptions of organizational reasoning.

A procedure should define:

* inputs;
* required organizational state;
* evidence requirements;
* ordered reasoning steps;
* applicable policies;
* authority requirements;
* constraints;
* possible outcomes;
* escalation paths;
* decision recording requirements.
Procedures should be accessible to agents through a stable OWM interface.

Example:

```
GET /owm/procedures/discount-approval
```

The agent runtime executes the procedure.

OWM provides the organizational model, rules, state, and decision semantics.

---

# **11. Agent Integration**

OWM is designed to be consumed by agents.

The agent should not need to understand how OWM internally stores information.

The interface should expose organizational capabilities such as:

```
resolve_entity()
get_entity_state()
get_relationships()
get_policy()
get_authority()
get_procedure()
check_constraints()
get_decisions()
record_decision()
get_evidence()
```

An agent should be able to ask:

What does the organization know about Acme?

What is the current state of Acme?

What policy applies?

Who has authority?

What procedure governs this decision?

What decisions have previously been made?

What evidence supports this fact?

The agent remains responsible for execution and interaction.

OWM remains responsible for organizational understanding.

---

# **12. Agent Runtime Boundary**

Sovera should **not build a proprietary general-purpose agent runtime as part of OWM**.

OWM should be runtime-agnostic.

An external runtime such as **Agno** may provide:

* agent execution;
* tool calling;
* model interaction;
* sessions;
* execution loops;
* multi-agent coordination;
* runtime memory.
Sovera provides:

* organizational identity;
* organizational state;
* organizational semantics;
* organizational policies;
* organizational procedures;
* organizational constraints;
* organizational decision memory.
This separation keeps the OWM product focused and allows the runtime ecosystem to evolve independently.

---

# **13. OWM API / Contract**

The OWM contract should become more important than the underlying implementation.

Conceptually:

```
OWM Contract
│
├── Entity
├── Identity
├── Relationship
├── State
├── Policy
├── Authority
├── Procedure
├── Constraint
├── Evidence
└── Decision
```

The implementation may evolve from:

```
Utopia / OG-RAG
```

to:

```
Sovera-native OWM
```

without changing the conceptual contract exposed to agents.

This abstraction is strategically important.

Utopia can serve as a knowledge foundation or experimental substrate without becoming a permanent architectural dependency.

---

# **14. Knowledge Foundation Integration**

The knowledge foundation is responsible for making enterprise evidence accessible.

Capabilities may include:

* document parsing;
* extraction;
* retrieval;
* semantic search;
* graph retrieval;
* structured database access;
* provenance;
* identity resolution;
* source synchronization.
OWM consumes this capability.

The relationship should be:

```
Knowledge Foundation
        ↓
Evidence
        ↓
OWM
        ↓
Organizational Understanding
        ↓
Agent
        ↓
Decision / Action
```

The knowledge foundation answers:

What evidence exists?

OWM answers:

What does that evidence mean within the organization?

And:

What organizational state, rule, procedure, or decision follows from it?

---

# **15. Reference Use Case**

## **Discount Approval**

Question:

Can we give Acme a 15% discount on its next NS-500 order?

OWM should resolve:

```
Customer
    Acme Manufacturing

Product
    NS-500 Industrial Controller

Contract
    ACME-MFG-2025
    Active

Exception
    NS-500
    Maximum 15%

Policy
    2026 Pricing Policy

Requestor
    Sarah Chen
    Enterprise AE

Authority
    AE ≤10%

Required Approver
    Michael Torres
    VP Sales
    >10% and ≤20%
```

Result:

```
APPROVE_WITH_AUTHORIZATION
```

The key product behavior is not merely producing the answer.

It is producing an answer grounded in an explicit organizational model.

---

# **16. Required Decision Vocabulary**

OWM should support a standardized decision vocabulary.

Initial set:

```
APPROVE
APPROVE_WITH_AUTHORIZATION
REJECT_OR_ESCALATE
REVIEW_REQUIRED
REQUEST_EVIDENCE
```

These are not merely agent responses.

They are organizational decision states that should be persisted and queryable.

---

# **17. Decision Persistence**

A major differentiator of OWM is that decisions persist.

After a decision is made, a future agent should be able to ask:

Have we made a similar decision before?

Why did we approve this customer exception?

Who approved it?

What authority did they use?

What policy was active at the time?

What evidence supported the decision?

Is that decision still valid under today’s policy?

This turns decisions into organizational memory rather than transient LLM output.

---

# **18. Historical Decision Semantics**

Historical decisions must remain historically accurate.

If policy changes:

```
2025:
AE ≤15%

2026:
AE ≤10%
```

A 2025 decision approved by an AE at 15% should not be rewritten as invalid simply because the current policy is different.

OWM should support:

```
Historical State
      +
Historical Policy
      +
Historical Authority
      +
Historical Evidence
      =
Historical Decision
```

Then separately determine:

```
Current State
      +
Current Policy
      +
Current Authority
      =
Current Decision Context
```

This distinction is fundamental to organizational memory.

---

# **19. Conflict Detection**

OWM must detect contradictions between evidence and organizational constraints.

Example:

```
Evidence:
Michael reports to Sarah.

Organizational constraint:
VP Sales cannot report to an Enterprise AE.

OWM:
CONFLICT

Status:
REQUIRES_REVIEW
```

The system should preserve the evidence rather than silently correcting it.

This establishes an important trust boundary:

**OWM can interpret evidence, but it must not silently rewrite organizational reality.**

---

# **20. Evaluation Framework**

OWM evaluation should move beyond simple question-answer accuracy.

The system should be evaluated across six dimensions.

## **20.1 Identity Accuracy**

Can OWM correctly resolve entities across systems?

---

## **20.2 State Accuracy**

Can OWM establish the correct organizational state for a given point in time?

---

## **20.3 Policy Accuracy**

Can OWM identify the applicable policy?

---

## **20.4 Authority Accuracy**

Can OWM determine who has authority to act?

---

## **20.5 Procedure Accuracy**

Can OWM apply the correct organizational procedure?

---

## **20.6 Decision Persistence**

Can a future agent retrieve and correctly use previous organizational decisions without reconstructing the entire original evidence set?

This final dimension is especially important.

---

# **21. Primary OWM Experiment**

The next major experiment should test **organizational memory**, rather than another generic RAG-vs-OWM accuracy comparison.

### **Phase 1**

Agent A answers:

Can Sarah give Acme a 15% discount?

The decision is persisted.

### **Phase 2**

Agent B receives a new question that depends on the previous decision.

Agent B should retrieve:

* previous decision;
* decision rationale;
* authority;
* evidence;
* timestamp;
* applicable policy;
* organizational state.
Agent B should not need to reread the entire original corpus.

### **Phase 3**

Change the organizational state.

For example:

```
2026 policy:
AE ≤10%

2027 policy:
AE ≤5%
```

Ask:

Does the previous decision remain historically valid?

and:

Would we make the same decision today?

OWM should distinguish the two.

This experiment directly tests the capability that ordinary evidence retrieval does not provide:

**durable organizational memory.**

---

# **22. Scalability**

The OWM model must operate from small synthetic domains to large enterprise environments.

Initial test:

```
10–100 entities
20–100 relationships
10–50 policies/procedures
10–50 documents
5–20 decision scenarios
```

Scale testing should subsequently introduce:

```
1,000+
10,000+
100,000+
```

facts and relationships.

The objective is not simply retrieval throughput.

The objective is maintaining:

* identity;
* temporal correctness;
* provenance;
* organizational constraints;
* policy applicability;
* decision consistency.
---

# **23. Security and Governance**

OWM must preserve enterprise governance boundaries.

Requirements:

* tenant isolation;
* RBAC;
* source-level permissions;
* role-aware access;
* provenance;
* audit logging;
* decision history;
* policy versioning;
* immutable decision records where required;
* encryption;
* configurable retention.
An agent must never receive organizational information that its identity and permissions do not authorize.

---

# **24. Observability**

OWM should integrate with Sovera’s existing agent identity, observability, and evaluation substrate.

Every agent interaction with OWM should be observable.

Trace:

```
Agent
  ↓
OWM Query
  ↓
Organizational Facts
  ↓
Evidence
  ↓
Policy
  ↓
Procedure
  ↓
Decision
```

This should allow operators to answer:

Why did the agent reach this organizational conclusion?

and:

Which organizational facts caused the decision?

---

# **25. Human Governance**

OWM should support human review when organizational truth is uncertain.

Examples:

```
CONFLICT DETECTED
```

```
REQUEST_EVIDENCE
```

```
AMBIGUOUS ENTITY
```

```
AUTHORITY UNCERTAIN
```

Human corrections should become governed organizational knowledge, with provenance and auditability.

The system should distinguish:

```
Machine inferred
Human confirmed
Human overridden
Source asserted
Agent proposed
```

---

# **26. OWM Lifecycle**

OWM should operate as a continuous learning system.

```
Enterprise Evidence
        ↓
Extraction
        ↓
Identity Resolution
        ↓
Organizational Interpretation
        ↓
Validation
        ↓
OWM State
        ↓
Agent Use
        ↓
Decision
        ↓
Decision Memory
        ↓
New Evidence
        ↓
Continuous Enrichment
```

The goal is an **evergreen organizational model**.

The model should become more useful as the organization generates:

* more evidence;
* more decisions;
* more exceptions;
* more procedures;
* more organizational history.
---

# **27. Initial Data Model**

The first OWM implementation should support:

### **Foundation objects**

```
Organization
Person
Employee
Department
Customer
Account
Product
Contract
Order
Evidence
```

### **OWM objects**

```
Role
Policy
PricingException
AuthorityBand
Procedure
Constraint
Approval
Decision
```

Relationships should include:

```
owns
reports_to
works_for
has_role
governs
applies_to
covered_by
authorized_by
approved_by
requested_by
related_to
supersedes
derived_from
supported_by
```

---

# **28. Initial Product Surface**

The initial OWM product should expose five major capabilities.

## **28.1 Explore**

Explore organizational entities, relationships, state, policies, and evidence.

## **28.2 Understand**

Ask questions about organizational meaning.

Example:

Why is Acme eligible for a 15% NS-500 discount?

## **28.3 Decide**

Run an organizational procedure.

Example:

Evaluate this discount request.

## **28.4 Explain**

Show the organizational reasoning and evidence behind a decision.

## **28.5 Remember**

Retrieve historical decisions and organizational precedent.

---

# **29. Non-Goals**

The following are explicitly out of scope for the initial OWM product:

### **General Agent Runtime**

Do not build:

* proprietary agent execution loops;
* general multi-agent orchestration;
* generalized tool execution;
* model routing infrastructure.
Use existing runtime capabilities where appropriate.

### **Generic RAG Platform**

Do not rebuild:

* document vectorization;
* generic search;
* generic chunking;
* generic retrieval infrastructure.
### **Enterprise Data Warehouse**

OWM should not become a replacement for operational systems or analytical warehouses.

### **Universal Ontology**

OWM should not attempt to define a universal ontology of business.

The ontology is organizational and domain-specific.

### **Autonomous Organizational Authority**

OWM should represent authority.

It should not invent authority.

---

# **30. MVP**

The MVP should demonstrate one complete organizational decision loop.

### **Domain**

Sales discount approval.

### **Required capabilities**

1. Enterprise entity model
2. Cross-system identity resolution
3. Temporal organizational state
4. Policy representation
5. Authority representation
6. Procedure representation
7. Constraint validation
8. Evidence provenance
9. Decision recording
10. Historical decision retrieval
11. Agent integration
12. Human review for conflicts

⠀
### **Demonstration**

An agent receives:

Can we give Acme a 15% discount on the NS-500?

OWM should:

```
Resolve Acme
       ↓
Resolve NS-500
       ↓
Establish active contract
       ↓
Establish applicable exception
       ↓
Establish current policy
       ↓
Establish requestor authority
       ↓
Determine required approver
       ↓
Return decision
       ↓
Record decision
```

---

# **31. Success Criteria**

OWM succeeds when it demonstrates capabilities that are difficult to obtain reliably by repeatedly searching raw enterprise evidence.

### **Core success criteria**

**1. Persistent understanding**

An organizational fact established once can be reused by future agents.

**2. Temporal understanding**

OWM can distinguish historical truth from current truth.

**3. Organizational authority**

OWM can determine who is permitted to act.

**4. Procedural understanding**

OWM can represent and execute organizational reasoning patterns.

**5. Constraint awareness**

OWM detects organizational contradictions instead of silently correcting them.

**6. Decision memory**

Previous decisions become reusable organizational knowledge.

**7. Provenance**

Every consequential organizational conclusion can be traced to supporting evidence and organizational rules.

**8. Runtime independence**

OWM remains useful regardless of which agent runtime executes the agent.

---

# **32. Strategic Differentiation**

The strategic distinction should not be:

```
OWM vs RAG
```

or:

```
OWM vs GraphRAG
```

Those comparisons are too narrow.

The distinction is:

```
Enterprise Evidence
        ↓
Knowledge Foundation
        ↓
Organizational Understanding
        ↓
Agent Execution
```

RAG and graph systems primarily improve access to and reasoning over information.

OWM provides a persistent representation of organizational meaning and state.

The resulting distinction is:

**The knowledge foundation remembers what the organization has said. OWM remembers how the organization works.**

---

# **33. Long-Term Vision**

OWM should evolve from a domain-specific organizational model into the semantic and decision substrate for enterprise AI.

Over time, the model should encompass:

```
People
Customers
Products
Processes
Policies
Contracts
Authority
Financial State
Operational State
Risk
Exceptions
Decisions
Organizational History
```

The result is not a “company brain.”

It is something more useful and more defensible:

**A continuously evolving computational model of the organization that AI can understand, query, reason against, and act through.**

---

# **34. Product Principle**

The most important product principle is:

**Do not make AI repeatedly reconstruct the organization from raw evidence if the organization can maintain that understanding once.**

Enterprise AI should not have to rediscover:

* who owns what;
* which customer is which;
* what policy applies;
* who has authority;
* which exception is active;
* how a process works;
* why a decision was made.
OWM should make that organizational understanding persistent.

---

# **35. Final Architecture**

```
ENTERPRISE
                            │
             ┌──────────────┴──────────────┐
             │                             │
        STRUCTURED                    UNSTRUCTURED
             │                             │
             └──────────────┬──────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ KNOWLEDGE FOUNDATION│
                 │                     │
                 │ Evidence            │
                 │ Retrieval           │
                 │ Identity            │
                 │ Provenance          │
                 └──────────┬──────────┘
                            │
                            ▼
              ╔════════════════════════════╗
              ║            OWM             ║
              ║                            ║
              ║ Domain Model               ║
              ║ Ontology                   ║
              ║ Organizational State       ║
              ║ Policy & Authority         ║
              ║ Procedures                 ║
              ║ Constraints                ║
              ║ Decision Memory             ║
              ║                            ║
              ║ Persistent • Governed      ║
              ║ Temporal • Provenanced     ║
              ╚══════════════╤═════════════╝
                             │
                             ▼
                    ┌─────────────────┐
                    │  AGENT RUNTIME  │
                    │                 │
                    │ Agno / Other    │
                    └────────┬────────┘
                             │
                             ▼
                     ACTIONS / DECISIONS
                             │
                             ▼
                       DECISION MEMORY
                             │
                             └──────────────► OWM
```

# **36. North Star**

Sovera OWM exists to make organizational understanding a first-class layer of enterprise AI.

**AI knows what’s in your data.** **OWM knows what it means to the organization.**

And over time:

**AI learns from the organization.** **OWM remembers how the organization works.**