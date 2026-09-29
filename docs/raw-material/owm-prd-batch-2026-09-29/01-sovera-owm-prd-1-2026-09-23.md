# Sovera OWM PRD - 1
#owm #owm-product-requirement
#gpt

Sep 23, 2026

# **Sovera OWM**

## **Product Requirements Document**

**Kind:** Product definition / architecture-aligned PRD
**Status:** PROPOSAL 
**Initiated By**: Mehul 
**Audience:** Product, engineering, design, AI/ML, data, security, operations, and future contributors
**Scope:** Organizational World Model kernel and the platform capabilities required to build, govern, query, and act upon organizational understanding
**Version:** 1.0

---

# **1. Product Summary**

Sovera OWM is a governed **Organizational World Model** that continuously builds a machine-interpretable representation of how an organization works.

It transforms heterogeneous enterprise information into persistent organizational understanding across:

* entities
* relationships
* concepts
* processes
* policies
* roles
* authority
* events
* decisions
* exceptions
* evidence
* semantic mappings
* temporal context

OWM is not another enterprise database, knowledge graph, or RAG index.

It is the **semantic kernel between enterprise information and AI**.

The platform combines:

1. Enterprise information ingestion and synchronization
2. Evidence extraction and provenance
3. Entity and semantic resolution
4. Organizational ontology and semantic contracts
5. A temporal semantic state graph
6. Organizational context assembly
7. Retrieval and reasoning
8. Decision intelligence
9. Governed action
10. Continuous learning and enrichment
11. Human review and governance
12. APIs, MCP, and agent access

⠀
The fundamental product loop is:

**Information → Evidence → Understanding → Decision → Action → Outcome → New Evidence → Better Understanding**

The goal is not simply to make enterprise information searchable.

The goal is to make the organization **understandable to AI**.

---

# **2. Problem Statement**

Enterprise AI has access to increasingly large amounts of organizational information.

The problem is that access to information is not the same as understanding.

An organization may contain:

* CRM accounts
* ERP customers
* contracts
* pricing policies
* employee directories
* SOPs
* support systems
* financial systems
* documents
* emails
* spreadsheets
* databases
* SaaS applications
* data warehouses
* operational events

The same entity may have different names and meanings across systems.

The same word may mean different things in different organizational contexts.

Policies may have exceptions.

Authorities depend on roles.

Roles change over time.

Business definitions conflict.

Facts become obsolete.

Decisions depend on combinations of structured and unstructured evidence.

Traditional enterprise AI approaches address individual parts of this problem:

* RAG retrieves information.
* GraphRAG retrieves connected information.
* Text-to-SQL queries structured data.
* Knowledge graphs represent relationships.
* Agents orchestrate tools and models.
* LLMs generate and reason.

None of these, by themselves, provides a durable representation of:
**How this particular organization works.**

> *Sovera OWM provides that missing layer.*

---

# **3. Product Vision**

Build the organizational understanding layer that allows AI systems to understand, reason about, and act within an enterprise.

OWM should optimize for:

1. **Understanding over retrieval**
2. **Evidence over unsupported assertions**
3. **Meaning over raw structure**
4. **Context over isolated facts**
5. **Temporal truth over current-state assumptions**
6. **Governance over silent automation**
7. **Reversible operations over destructive mutation**
8. **Explicit uncertainty over false certainty**
9. **Composable intelligence over monolithic agents**
10. **Continuous enrichment over one-time knowledge ingestion**
⠀
The long-term product vision is:

**Every enterprise has an OWM that becomes a living, continuously improving representation of how the organization works.**

---

# **4. Core Product Thesis**

### **Models provide intelligence.**

### **Enterprise systems provide information and capabilities.**

### **OWM provides organizational understanding.**

RAG retrieves.
GraphRAG connects.
Text-to-SQL queries.
Agents act.

**OWM understands.**

Sovera combines these capabilities around a persistent organizational semantic layer.

---

# **5. Goals**

## **5.1 Primary Goals**

Sovera OWM shall:

1. Build a durable semantic representation of an organization.
2. Ingest information from heterogeneous enterprise systems.
3. Preserve evidence for every consequential assertion.
4. Resolve entities across systems.
5. Resolve organizational meaning across systems and domains.
6. Represent temporal state and historical organizational understanding.
7. Model organizational concepts, policies, processes, roles, authority, decisions, and exceptions.
8. Support governed ontology and semantic-contract evolution.
9. Assemble context for organizational questions.
10. Support retrieval and reasoning over organizational state.
11. Provide a first-class decision engine interface.
12. Support typed decisions with explicit confidence and evidence.
13. Gate consequential actions through policy and authority.
14. Record decisions, reasoning context, actions, and outcomes.
15. Learn from new evidence, human corrections, decisions, and outcomes.
16. Expose organizational understanding to agents, BI, search, automation, and applications.
17. Preserve auditability and provenance throughout the lifecycle.
18. Allow organizations to control deployment, models, data, and semantic assets.

⠀
---

# **6. Non-Goals**

Sovera OWM is not intended to be:

1. A replacement for CRM, ERP, HRIS, financial, or operational systems.
2. A general-purpose transactional database.
3. A document management system.
4. A generic vector database.
5. A conventional enterprise search product.
6. A knowledge graph whose primary purpose is graph visualization.
7. A monolithic autonomous agent.
8. A system where LLM output becomes organizational truth automatically.
9. A system where extraction directly mutates semantic state without governance.
10. A mandatory replacement for existing enterprise data infrastructure.
11. A proprietary model platform that requires a single model provider.
12. A closed ecosystem that prevents customers from exporting their organizational understanding.

⠀
The OWM owns **meaning and organizational state**. Existing enterprise systems continue to own their operational systems of record.

---

# **7. Users and Personas**

## **7.1 OWM Administrator**

Responsible for configuring an organization’s OWM.

Needs to:

* configure sources
* manage semantic domains
* configure ontology
* manage mappings
* configure governance policies
* manage users and permissions
* configure models
* inspect system health
* manage review workflows
* export organizational state
---

## **7.2 Knowledge / Semantic Steward**

Responsible for maintaining organizational meaning.

Needs to:
* review entity matches
* resolve semantic conflicts
* approve concepts
* review policy interpretations
* manage mappings
* inspect evidence
* review proposed organizational knowledge
* understand why the system reached a conclusion
---

## **7.3 Business User**

Needs to:
* ask questions
* search organizational knowledge
* understand policies
* inspect relationships
* explore organizational context
* understand why an answer or decision was produced
---

## **7.4 AI / Automation Builder**

Needs to:
* retrieve organizational context
* query semantic state
* invoke decision capabilities
* connect agents to OWM
* expose OWM context to AI applications
* build workflows around governed decisions
---

## **7.5 Agent / External Client**

Needs authenticated, permission-scoped access to:
* organizational context
* entities
* relationships
* policies
* processes
* evidence
* decisions
* authorized data sources
* decision engines
* governed actions
---

## **7.6 Governance / Risk Owner**

Needs to:
* inspect consequential decisions
* understand evidence
* inspect confidence
* review authority
* replay organizational state at decision time
* identify policy violations
* understand overrides
* audit actions
---

# **8. Core Conceptual Model**

OWM should treat the following as first-class semantic primitives.

## **8.1 Entity**

A real organizational object.

Examples:
* Customer
* Account
* Employee
* Vendor
* Product
* Contract
* Business Unit
* Location
---

## **8.2 Relationship**

A meaningful relationship between entities.

Examples:
* Customer → owns → Contract
* Employee → reports_to → Manager
* Account → belongs_to → Territory
* Product → covered_by → Policy
---

## **8.3 Concept**

An organizational meaning or definition.

Examples:
* Strategic Account
* Enterprise Customer
* Active Customer
* At-Risk Customer
* Approved Vendor
Concepts may be domain-specific and context-dependent.

---

## **8.4 Attribute**

A property associated with an entity or relationship.

---

## **8.5 Event**

Something that happened.

Examples:
* Contract signed
* Invoice issued
* Customer escalated
* Employee promoted
* Policy changed
---

## **8.6 Process**

A sequence or structured pattern through which the organization operates.

Examples:
* Customer onboarding
* Discount approval
* Procurement
* Incident escalation
* Employee promotion
---

## **8.7 Policy**

A rule governing organizational behavior.

A policy must support:
* scope
* effective period
* authority
* exceptions
* source
* version
* applicability conditions
---

## **8.8 Role and Authority**

OWM must represent:
* organizational roles
* responsibilities
* authority
* delegation
* reporting relationships
* authorization boundaries
* temporal validity
---

## **8.9 Decision**

A decision is a first-class organizational object.

It records:
* decision question
* subject
* organizational context
* applicable policies
* evidence
* candidate outcomes
* selected outcome
* confidence
* decision engine
* decision time
* authority
* resulting action
* outcome
---

## **8.10 Exception**

An exception modifies normal organizational behavior.

Examples:
* Contract-specific pricing
* Temporary approval authority
* Customer-specific SLA
* Policy exemption
* Special procurement rule
Exceptions must not be flattened into general rules.

---

## **8.11 Evidence**

Evidence is the concrete source material supporting an organizational assertion.

Evidence may reference:
* document
* page
* paragraph
* table cell
* database row
* API response
* email
* event
* source-system record
Evidence is distinct from provenance.

**Provenance answers: where did this assertion come from?**

**Evidence answers: what specifically supports it?**

---

## **8.12 Semantic Mapping**

A semantic mapping connects source-system concepts to OWM concepts.

Example:

```
Salesforce.Account
SAP.Customer
Zendesk.Organization
Contract.Counterparty
        ↓
      OWM
        ↓
     Customer
```

Mappings must remain distinct from asserted organizational facts.

---

# **9. Organizational State**

OWM must maintain a representation of organizational state over time.

Every applicable assertion should distinguish:

### **World / Valid Time**

When the assertion was true in the organization.

### **Recording Time**

When Sovera learned or accepted the assertion.

This enables questions such as:

What did we know about Acme when the decision was made?

rather than only:

What does OWM believe today?

Historical organizational state must be replayable where supported.

---

# **10. Evidence and Understanding Lifecycle**

The primary ingestion-to-understanding lifecycle is:

```
Enterprise Information
        ↓
Source Parsing / Perception
        ↓
Evidence
        ↓
Semantic Extraction
        ↓
Proposal
        ↓
Validation
        ↓
Entity Resolution
        ↓
Semantic Resolution
        ↓
Governance / Review
        ↓
OWM Semantic State
```

Important constraint:

**Extraction never writes directly into OWM semantic state.**

Extraction produces evidence-backed proposals.

Governance promotes proposals into organizational understanding.

This protects OWM from uncontrolled model-generated mutations.

---

# **11. Organizational Understanding**

OWM should progressively construct organizational understanding across five dimensions.

### **WHAT**

Entities and concepts.

### **HOW**

Processes and relationships.

### **WHY**

Policies, decisions, and business rules.

### **WHO**

Roles, authority, ownership, and responsibility.

### **WHEN**

Temporal validity, events, history, and context.

Together:

**What + How + Why + Who + When = Organizational Understanding**

---

# **12. Semantic Contract**

The organization’s semantic model should be treated as a governed contract.

It defines:

* concepts
* entities
* relationships
* properties
* domains
* constraints
* temporal semantics
* policies
* authority
* process semantics
* evidence requirements
* mappings
* aliases
* semantic relationships
New concepts or relationships discovered by extraction become **proposals**, not silent ontology mutations.

Semantic changes must be:

* inspectable
* versioned
* attributable
* reversible where applicable
---

# **13. Entity Resolution**

OWM shall resolve entities across organizational systems.

Resolution should consider:

* exact identifiers
* canonical names
* aliases
* similarity
* entity type
* contextual relationships
* supporting evidence
The system should prefer a false split over an unsafe merge when confidence is insufficient.

Ambiguous matches should enter a review workflow.

Merges must be reversible and preserve historical identity.

---

# **14. Semantic Resolution**

Entity resolution is insufficient.

OWM must also resolve meaning.

Example:

```
CRM:     Customer
ERP:     Customer
Support: Client
Finance: Account
Marketing: Enterprise Customer
Legal:   Counterparty
```

These may refer to the same organizational concept—or different concepts depending on context.

Semantic resolution must therefore consider:

* source
* domain
* context
* definition
* usage
* relationships
* evidence
* temporal validity
This is one of the defining capabilities of OWM.

---

# **15. Context Assembly**

OWM shall provide a context assembly service.

Input:

```
Question / Intent
```

Output:

```
Organizational Context
```

A context bundle may contain:

* entities
* concepts
* relationships
* policies
* processes
* roles
* authority
* exceptions
* temporal state
* evidence
* semantic mappings
* relevant structured data
* relevant documents
Context assembly should be:

* permission-aware
* evidence-aware
* temporal
* deterministic where possible
* bounded
* reproducible
* traceable
---

# **16. Retrieval and Reasoning**

OWM should not attempt to replace retrieval systems.

Instead:

**OWM owns meaning. Retrieval owns discovery. Models own generation.**

Supported retrieval mechanisms may include:

* full-text retrieval
* vector retrieval
* hybrid retrieval
* graph traversal
* OG-RAG
* structured queries
* Text-to-SQL
* source-system queries
Retrieval should be grounded in OWM semantics where organizational meaning is required.

---

# **17. Decision Intelligence**

Decision intelligence is a first-class OWM capability.

The system should distinguish:

### **Understanding**

What does the organization believe?

### **Judgment**

Given that understanding, what outcome is appropriate?

### **Action**

What should the system do?

These should not be collapsed into one LLM prompt.

---

# **18. Decision Engine**

Sovera shall define a provider-neutral Decision Engine interface.

Conceptually:

```
DecisionResult decide(
    DecisionQuestion question,
    ContextBundle context,
    list[Outcome] outcomes
)
```

A Decision Engine returns:

* candidate outcome
* probability distribution
* confidence
* supporting evidence
* model/provider
* timestamp
* decision metadata

Possible implementations include:

* deterministic rules
* TypeSafe / System One models
* conventional ML models
* LLM-based judgment
* domain-specific models
* human decision
* composite decision engines

TypeSafe is therefore an **implementation of the decision layer**, not a dependency of OWM.

---

# **19. Typed Decisions**

Decisions should be expressed as typed outcomes rather than requiring free-form natural-language generation.

Example:

```
Question:
Can Acme receive a 15% discount?

Possible outcomes:

APPROVE
APPROVE_WITH_AUTHORIZATION
REJECT
ESCALATE
```

The Decision Engine returns:

```
APPROVE                     0.03
APPROVE_WITH_AUTHORIZATION  0.91
REJECT                      0.02
ESCALATE                    0.04
```

Sovera then applies deterministic governance rules.

For example:

```
IF outcome = APPROVE_WITH_AUTHORIZATION
AND authority = VP_SALES
THEN route approval to VP_SALES
```

This creates a separation between:

**probabilistic judgment**

and

**deterministic execution.**

---

# **20. Decision Governance**

No consequential action should depend solely on model confidence.

A decision may require:

* sufficient evidence
* applicable policy
* valid authority
* acceptable confidence
* current organizational state
* required approvals
* absence of unresolved conflicts
Decision gates may produce:

```
ACT
ROUTE
ESCALATE
REQUEST_EVIDENCE
REJECT
HUMAN_REVIEW
```

---

# **21. Decision Record**

Every consequential decision should create a durable Decision Record.

The record should contain:

```
Decision ID
Question
Subject
Organizational Context
Evidence
Applicable Policies
Applicable Exceptions
Authority
Candidate Outcomes
Selected Outcome
Probabilities
Confidence
Decision Engine
Model Version
Decision Timestamp
World-Time Context
Recording-Time Context
Action
Actor
Outcome
Override / Review
```

This enables:

**“Why did the system make that decision?”**

and:

**“What did the system know when it made that decision?”**

---

# **22. Decision Replay**

Sovera should support replaying the organizational state surrounding a historical decision.

Example:

Why did Sovera approve this discount on August 4?

Replay should reconstruct, where possible:

```
OWM state
+
evidence available at the time
+
applicable policy version
+
authority state
+
decision context
+
decision engine
=
historical decision context
```

This is critical for regulated, financial, operational, and high-consequence workflows.

---

# **23. Governed Action**

OWM itself should not become a transactional execution system.

Instead:

```
OWM
 ↓
Decision
 ↓
Governance Gate
 ↓
Authorized Action
 ↓
External System
```

Actions should be exposed through explicit capabilities.

Examples:

* approve discount
* create CRM task
* route invoice
* escalate ticket
* update workflow status
* notify approver

Every write-capable action must be:

* explicitly authorized
* permission-scoped
* auditable
* attributable
* reversible where possible
* policy-controlled
---

# **24. Continuous Learning**

The OWM should improve over time through:

* new evidence
* source changes
* entity corrections
* semantic corrections
* policy changes
* human review
* decision outcomes
* overrides
* exceptions
* agent interactions
Core loop:

```
Information
    ↓
Evidence
    ↓
Understanding
    ↓
Decision
    ↓
Action
    ↓
Outcome
    ↓
New Evidence
    ↓
Better Understanding
```

The organizational model is therefore a **living asset**, not a static knowledge graph.

---

# **25. Core User Journeys**

## **25.1 Establish an OWM**

1. Create organization/workspace.
2. Connect enterprise sources.
3. Select or define semantic domains.
4. Establish initial ontology/semantic contract.
5. Begin evidence ingestion.
6. Generate semantic proposals.
7. Resolve entities and meanings.
8. Review proposals.
9. Promote accepted understanding.
10. OWM becomes queryable.

⠀
### **Acceptance Criteria**

* Sources can be connected independently.
* Evidence is retained.
* Extraction cannot directly mutate OWM.
* Semantic proposals are inspectable.
* Every promoted assertion has provenance.
* OWM state is permission-aware.
---

# **26. User Journey: Teach OWM a New Policy**

1. User adds a new policy document.
2. Document becomes searchable.
3. Document is parsed.
4. Evidence is extracted.
5. Candidate policy semantics are generated.
6. Applicable concepts/entities are resolved.
7. Proposed policy enters review.
8. Reviewer approves.
9. Policy becomes part of OWM.
10. Relevant decisions automatically use the new policy.

⠀
### **Acceptance Criteria**

* Existing policy remains historically valid where applicable.
* New policy has effective dates.
* Policy source is inspectable.
* Affected decisions can discover the new policy.
* No unrelated organizational semantics are silently modified.
---

# **27. User Journey: Ask an Organizational Question**

User asks:

Who can approve a 15% discount for Acme?

System:

1. Interprets semantic intent.
2. Resolves Acme.
3. Retrieves applicable concepts.
4. Determines pricing policy.
5. Resolves contract exceptions.
6. Resolves authority.
7. Assembles organizational context.
8. Retrieves supporting evidence.
9. Generates answer.
10. Provides citations and temporal context.

⠀
---

# **28. User Journey: Make a Decision**

User asks:

Can we give Acme a 15% discount?

System:

```
Question
 ↓
Semantic Intent
 ↓
OWM Grounding
 ↓
Context Bundle
 ↓
Applicable Policies
 ↓
Exceptions
 ↓
Authority
 ↓
Decision Engine
 ↓
Typed Decision
 ↓
Governance Gate
 ↓
Action / Escalation
```

Example result:

```
Decision:
APPROVE_WITH_AUTHORIZATION

Confidence:
0.91

Required authority:
VP Sales

Reason:
Acme has a contractual exception allowing discounts
above the standard 10% threshold, but current policy
requires VP Sales approval for discounts above 10%.

Evidence:
3 sources
7 organizational facts
1 contract exception
1 current policy
1 authority relationship
```

---

# **29. User Journey: Resolve Conflicting Definitions**

Example:

```
Sales:
Enterprise Customer = ARR > $1M

Finance:
Enterprise Customer = ARR > $5M

Marketing:
Enterprise Customer = >1,000 employees
```

OWM must not collapse these into one “correct” definition.

Instead it preserves:

```
Concept
Enterprise Customer

Context:
Sales
Definition:
ARR > $1M

Context:
Finance
Definition:
ARR > $5M

Context:
Marketing
Definition:
>1,000 employees
```

AI can then reason appropriately depending on the question and organizational context.

---

# **30. User Journey: Historical Decision Replay**

User asks:

Why did we reject this vendor in March?

System reconstructs:

* organizational state
* evidence available at the time
* vendor profile
* applicable policy
* risk assessment
* authority
* decision
* confidence
* subsequent override, if any
The system must not silently substitute today’s understanding for historical state.

---

# **31. Functional Requirements**

## **31.1 Organization and Access**

The system shall support:

* organizations
* workspaces
* users
* roles
* groups
* permissions
* SSO/OIDC
* service identities
* source-level authorization
* semantic-domain authorization

Authorization must apply consistently to:

* APIs
* UI
* graph reads
* evidence
* retrieval
* tools
* MCP
* decisions
* actions
* exports
---

# **32. Source Management**

The system shall support source adapters for:

* databases
* SaaS applications
* cloud storage
* documents
* object stores
* APIs
* event streams
* email
* enterprise repositories

Sources should maintain:

* source identity
* synchronization state
* observation history
* credentials
* permissions
* freshness
* deletion state
---

# **33. Evidence Layer**

The evidence layer shall preserve:

* source
* source identifier
* content location
* document identifier
* page
* paragraph
* table cell
* database row
* API response
* source timestamp
* retrieval timestamp
* content hash
* extracted span
* original content where permitted

Evidence must remain addressable.

---

# **34. Semantic Extraction**

Extraction shall support:

* entities
* relationships
* concepts
* attributes
* events
* policies
* processes
* roles
* authority
* decisions
* exceptions
* temporal assertions
* evidence

Extraction output is always a proposal.

---

# **35. Semantic Validation**

The system shall validate:

* entity types
* relation signatures
* concept compatibility
* policy applicability
* temporal consistency
* required evidence
* semantic contract constraints

Invalid proposals should be dropped or routed to review with explicit reasons.

---

# **36. Organizational Graph**

OWM shall support:

* temporal facts
* relationships
* concepts
* policy links
* authority relationships
* event relationships
* provenance
* evidence references
* derived understanding
* semantic mappings

The graph is a representation of organizational semantics, not the product itself.

---

# **37. Reasoning**

The reasoning layer may support:

* graph traversal
* rule evaluation
* constraint checking
* derived relationships
* OG-RAG
* semantic retrieval
* structured queries
* Text-to-SQL
* model reasoning

Derived knowledge must remain distinguishable from asserted knowledge.

---

# **38. Decision Engine API**

Sovera shall expose a provider-neutral Decision Engine contract.

A decision request should contain:

```
Decision Question
Subject
Context Bundle
Candidate Outcomes
Decision Policy
Evidence Requirements
Confidence Threshold
Authority Requirements
```

A result should contain:

```
Outcome
Probability Distribution
Confidence
Evidence References
Decision Engine
Model
Model Version
Timestamp
```

The architecture must permit multiple decision engines.

---

# **39. Decision Policy**

Decision policies define:

* which decisions may be automated
* required confidence
* required evidence
* required authority
* escalation thresholds
* human-review requirements
* allowed actions
Example:

```
Discount > 10%
AND
confidence < 0.90
→ HUMAN_REVIEW

Discount > 10%
AND
confidence >= 0.90
AND
VP authority confirmed
→ APPROVAL_REQUEST
```

---

# **40. Decision Engine Implementations**

Initial architecture should support:

### **Rules Engine**

For deterministic organizational policies.

### **LLM Decision Engine**

For semantic judgments requiring open-ended reasoning.

### **TypeSafe Decision Engine**

For typed probabilistic judgments over organizational context.

### **Human Decision Engine**

For explicit human adjudication.

### **Composite Decision Engine**

For combining:

```
Rules
+
TypeSafe
+
LLM
+
Human
```

This makes the decision layer extensible without changing OWM.

---

# **41. Search and Conversational Intelligence**

Sovera shall support:

* semantic search
* full-text search
* vector search
* hybrid retrieval
* graph traversal
* OG-RAG
* conversational answers
* organizational context queries

Answers should expose:

* evidence
* provenance
* relevant temporal context
* semantic context
* confidence where appropriate
---

# **42. Agent Interface**

Agents should be able to:

* search OWM
* inspect entities
* retrieve context
* inspect policies
* inspect authority
* retrieve evidence
* query structured systems
* invoke decision engines
* request human review
* invoke governed actions

Agents should not be granted unrestricted ability to mutate OWM or external systems.

---

# **43. MCP**

Sovera should expose OWM capabilities through MCP.

Potential tools:

```
search_organization
get_entity
get_context
get_policy
get_process
get_authority
get_evidence
get_decision_context
evaluate_decision
request_review
execute_authorized_action
```

All tools must enforce authorization.

---

# **44. Review and Governance**

The review system shall support queues for:

* ambiguous entities
* semantic conflicts
* ontology proposals
* policy proposals
* evidence insufficiency
* low-confidence decisions
* authority conflicts
* contradictory facts
* risky automated actions

Actions should include:

* accept
* reject
* merge
* keep separate
* revise
* defer
* escalate
* revert

Every consequential action must record:

* actor
* timestamp
* object
* reason
* previous state
* resulting state
---

# **45. UX Requirements**

The OWM console should provide:

1. Organization / workspace
2. Organizational map
3. Entities
4. Relationships
5. Semantic domains
6. Ontology / semantic contract
7. Evidence
8. Policies
9. Processes
10. Decisions
11. Decision replay
12. Review queue
13. Sources
14. Search
15. AI assistant
16. Agents
17. Actions
18. Audit
19. Members and permissions
20. System health

⠀
UX principles:

* Always expose evidence for consequential understanding.
* Distinguish asserted, proposed, derived, rejected, superseded, and inferred states.
* Make temporal scope visible.
* Make uncertainty visible.
* Make authority visible when decisions are involved.
* Prefer explicit governance over silent mutation.
* Make system failures actionable.
* Make historical state understandable.
---

# **46. Non-Functional Requirements**

## **Reliability**

* Idempotent ingestion
* Retryable jobs
* Persistent job state
* Safe concurrent processing
* No stale-worker resurrection
* Recoverable indexes
* External model failures must not corrupt OWM
## **Security**

* Strong authentication
* Fine-grained authorization
* Source-level permissions
* Encryption of credentials
* Audit logging
* Secure secrets
* Tenant isolation
## **Observability**

Expose:

* source freshness
* ingestion state
* evidence volume
* extraction failures
* proposal backlog
* review backlog
* entity-resolution statistics
* semantic conflicts
* model failures
* decision latency
* decision confidence
* human escalation rate
* action failures
---

# **47. Performance**

Initial product targets should prioritize:

### **Time to first understanding**

A source should become searchable before complete semantic enrichment.

### **Time to useful context**

Common organizational questions should retrieve relevant OWM context quickly.

### **Decision latency**

Typed decisions should be significantly cheaper and faster than unconstrained agentic reasoning where applicable.

### **Incremental enrichment**

Adding a new source should enrich existing organizational understanding rather than require a full rebuild.

Concrete production latency and scale targets should be established through workload benchmarking before becoming hard commitments.

---

# **48. Success Metrics**

## **Organizational Understanding**

* Percentage of entities successfully resolved across systems
* Percentage of consequential assertions with evidence
* Semantic mapping coverage
* Policy coverage
* Process coverage
* Authority coverage
* Percentage of organizational concepts with explicit definitions
* Semantic conflict resolution time
## **Knowledge Quality**

* Evidence-backed assertion rate
* Extraction acceptance rate
* Entity merge/revert rate
* Semantic proposal acceptance rate
* Contradiction rate
* Stale-knowledge rate
## **Decision Intelligence**

* Percentage of decisions with complete context
* Percentage with complete evidence
* Human escalation rate
* Automated decision rate
* Decision override rate
* Decision replay success rate
* Decision accuracy / outcome quality
* Confidence calibration
* Time from decision request to action
## **Platform Adoption**

* Time to first connected source
* Time to first useful organizational question
* Time to first governed decision
* Weekly active users
* Active AI applications
* Active agents
* Number of decision workflows
* Number of organizational domains modeled
## **Compounding Asset**

Most strategically:

**Growth in organizational understanding over time.**

Measure:

* number of resolved concepts
* number of mapped source concepts
* number of validated policies
* number of modeled processes
* number of authority relationships
* number of evidence-backed decisions
* number of reusable organizational contexts
---

# **49. Release Slices**

## **Slice A — Evidence Substrate**

* Source adapters
* Document ingestion
* Evidence model
* Provenance
* Search
* Source synchronization
* Evidence viewer
**Outcome:** Enterprise information becomes addressable evidence.

---

## **Slice B — Semantic Understanding**

* Entity model
* Relationship model
* Concept model
* Entity resolution
* Semantic mapping
* Ontology / semantic contract
* Proposal workflow
* Review queue
**Outcome:** Evidence becomes organizational understanding.

---

## **Slice C — Temporal OWM**

* Bitemporal assertions
* Historical state
* Policy validity
* Role/authority validity
* Event model
* Exception model
* Historical context assembly
**Outcome:** OWM understands how the organization changes over time.

---

## **Slice D — Organizational Context**

* Semantic intent
* Context assembly
* Graph traversal
* OG-RAG
* Structured query integration
* Text-to-SQL grounding
* Agent access
* MCP
**Outcome:** AI can query organizational understanding.

---

## **Slice E — Decision Intelligence**

* Decision object
* Decision Engine interface
* Decision policies
* Typed outcomes
* Confidence
* Evidence requirements
* TypeSafe adapter
* Rules adapter
* LLM adapter
* Human decision adapter
**Outcome:** AI can make governed judgments from organizational context.

---

## **Slice F — Governed Action**

* Action registry
* Authorization
* Policy gates
* Human approval
* External-system writes
* Action audit
* Reversibility
* Outcome capture
**Outcome:** Organizational understanding becomes governed action.

---

## **Slice G — Organizational Learning**

* Outcome capture
* Decision replay
* Overrides
* Feedback
* Semantic corrections
* Policy evolution
* Automated enrichment
* Organizational learning metrics
**Outcome:** OWM becomes a continuously compounding organizational asset.

---

# **50. Reference Architecture**

```
SOVERA AI EXPERIENCES
        ┌───────────┬───────────┬───────────┐
        │   Agents  │    BI     │ Automation│
        └───────────┴───────────┴───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Intelligence Layer  │
              │                      │
              │ Retrieval / Reasoning│
              │ Decision Engine      │
              │ Action / Governance  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │        OWM           │
              │                      │
              │ Entities             │
              │ Relationships        │
              │ Concepts             │
              │ Processes            │
              │ Policies             │
              │ Roles / Authority    │
              │ Events / Decisions   │
              │ Exceptions           │
              │ Temporal State       │
              │ Semantic Mappings    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Evidence Layer     │
              │                      │
              │ Documents            │
              │ Databases            │
              │ SaaS                 │
              │ APIs                 │
              │ Email                │
              │ Events               │
              └──────────────────────┘
```

The architectural principle is:

**Sources provide information. Evidence establishes what supports it. OWM establishes meaning. Decision engines evaluate possibilities. Governance determines what may happen. Actions change the world. Outcomes teach the model.**

---

# **51. Example: Acme Discount**

The canonical end-to-end demonstration should be:

**Can we give Acme a 15% discount?**

Enterprise information:

```
CRM
ERP
Contract
Pricing Policy
Org Directory
SOP
Email
```

becomes:

```
OWM

Acme
 ├── Customer
 ├── Strategic Account
 ├── Enterprise Pricing Tier
 ├── Contract
 │    └── Discount Exception
 ├── Current Pricing Policy
 │    └── >10% requires VP approval
 └── Account Authority
      └── VP Sales
```

OWM produces:

```
Organizational Context
```

Decision Engine evaluates:

```
APPROVE
APPROVE_WITH_AUTHORIZATION
REJECT
ESCALATE
```

Governance evaluates:

```
Evidence sufficient?
Policy applicable?
Exception valid?
Authority confirmed?
Confidence sufficient?
```

Result:

```
APPROVE_WITH_AUTHORIZATION
```

Action:

```
Route approval to VP Sales
```

Outcome:

```
Approved
```

Learning:

```
Decision + outcome become organizational evidence.
```

This is the product loop in miniature.

---

# **52. Strategic Differentiation**

Sovera should not position OWM as:

“A better knowledge graph.”

Nor:

“RAG with a graph.”

Nor:

“An enterprise ontology.”

Nor:

“An agent platform.”

The product category is:

**Organizational understanding for AI.**

The technical implementation includes:

* knowledge graphs
* ontology
* semantic mapping
* RAG
* OG-RAG
* structured queries
* agents
* decision engines
* probabilistic models
* policy engines
But these are implementation mechanisms beneath the product thesis.

The durable product asset is:

**The organization’s continuously evolving semantic state.**

---

# **53. Architectural Principles**

## **Principle 1 — OWM owns meaning**

Retrieval, models, and applications consume organizational meaning.

---

## **Principle 2 — Evidence before assertion**

No consequential organizational understanding without traceable support.

---

## **Principle 3 — Proposals before promotion**

AI can propose organizational knowledge.

Governance promotes it.

---

## **Principle 4 — Temporal truth matters**

An organization is not static.

OWM must represent how organizational understanding changes.

---

## **Principle 5 — Context before decision**

A decision engine should not be expected to reconstruct the organization from raw enterprise data.

OWM provides the context.

---

## **Principle 6 — Judgment and execution are different**

Probabilistic intelligence determines what appears appropriate.

Deterministic governance determines what the system is allowed to do.

---

## **Principle 7 — Uncertainty is a first-class signal**

Low confidence should produce escalation, not fabricated certainty.

---

## **Principle 8 — Decisions are organizational knowledge**

Consequential decisions and their outcomes should enrich OWM.

---

## **Principle 9 — The kernel is vendor-neutral**

OWM must not depend on a particular:

* LLM
* graph database
* vector database
* extraction framework
* decision model
* agent framework
These are replaceable implementation components.

---

## **Principle 10 — The OWM compounds**

Every validated mapping, policy, exception, decision, and correction should make the organization’s AI systems more capable.

---

# **54. Key Risks**

|  **Risk**  |  **Consequence**  |  **Mitigation**  | 
|---|---|---|
|  Incorrect entity merge  |  Organizational facts become mixed  |  Conservative resolution, review, reversible merges  |
|  Incorrect semantic mapping  |  AI reasons over the wrong meaning  |  Evidence, confidence, contextual mappings  |
|  Unsupported assertion  |  AI makes decisions on false organizational state  |  Evidence requirements  |
|  Stale policy  |  Incorrect decision  |  Temporal validity  |
|  Conflicting definitions  |  Incorrect interpretation  |  Context-specific concepts  |
|  LLM hallucination  |  Unsupported understanding  |  Structured proposals + evidence  |
|  Over-automation  |  Unsafe action  |  Governance gates + human review  |
|  Poor confidence calibration  |  Excessive autonomous decisions  |  Decision calibration + thresholds  |
|  Incorrect authority  |  Unauthorized action  |  Explicit authority model  |
|  Historical state corruption  |  Impossible decision replay  |  Bitemporal state  |
|  Decision engine lock-in  |  Architecture constrained by provider  |  Provider-neutral Decision Engine  |
|  OWM becomes monolithic  |  Slow evolution  |  Clean domain/service boundaries  |
|  Semantic model becomes over-engineered  |  Low adoption  |  Build around real organizational questions  |
|  Graph becomes the product  |  Technical complexity obscures value  |  Keep OWM semantics above storage technology  |
---

# **55. Open Product Questions**

The following should be explicitly resolved before production commitments:

1. Which organizational domains are highest priority?
2. Which semantic primitives are mandatory for the first production release?
3. What is the minimum viable OWM?
4. Which source systems are first-class integrations?
5. Which ontology standards should be supported initially?
6. What is the required degree of bitemporality?
7. What decisions can be automated?
8. Which decision classes require human approval?
9. What confidence thresholds are acceptable by decision type?
10. How should confidence calibration be evaluated?
11. Which actions may eventually write to external systems?
12. How should policy conflicts be resolved?
13. How should human decisions interact with automated decisions?
14. What constitutes sufficient evidence for a decision?
15. What organizational state must be replayable?
16. Which decision engines should be supported initially?
17. Should TypeSafe be an optional integration or first-class reference implementation?
18. How should customers export their OWM?
19. What is the organizational model’s retention policy?
20. How should semantic ownership be assigned across departments?

⠀
---

# **56. First Production Milestone**

The first meaningful production milestone should not be:

“We have built a knowledge graph.”

It should be:

**“Sovera can answer and make a governed organizational decision that existing enterprise AI cannot reliably make.”**

The minimum compelling flow is:

```
Connect sources
      ↓
Extract evidence
      ↓
Build OWM
      ↓
Resolve entities + meaning
      ↓
Understand policy + authority
      ↓
Assemble organizational context
      ↓
Make typed decision
      ↓
Apply governance
      ↓
Take or route action
      ↓
Record outcome
```

The canonical demonstration:

**Can we give Acme a 15% discount?**

If Sovera can answer that question with evidence, temporal context, policy, authority, confidence, and an appropriate action path, it demonstrates the central product thesis.

---

# **57. Product North Star**

The ultimate measure of OWM is not:

How many documents have we indexed?

Nor:

How many nodes are in the graph?

Nor:

How many tokens did the model process?

The North Star is:

**How much of the organization’s meaning can AI reliably understand, reason about, and act upon?**

And the strategic asset is:

**An organizational understanding that becomes richer, more accurate, more contextual, and more useful every time the organization interacts with Sovera.**

---

# **58. The Sovera OWM Thesis**

Organizations have spent decades building systems that record what happened.

They are now giving AI access to those systems.

The next layer is teaching AI:

**what those records mean, how the organization works, who has authority, which policies apply, what exceptions exist, what was true when, and what decisions should follow.**

That is the role of the Organizational World Model.

**Sovera gives AI an understanding of how your organization works.**