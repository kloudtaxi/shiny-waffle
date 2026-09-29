## **Sovera OWM PRD 2**

## **Superseding Product Requirements Document**

**Status:** Supersedes previous OWM PRD
**Version:** 2.0
**Date:** September 27, 2026
**Product:** Sovera OWM
**Architecture:** OWM + Agentic Execution Layer
**Agent Runtime:** Agno
**Primary Audience:** CTO, CIO, Chief AI Officer, Head of AI/Data/Automation, Enterprise Architect

---

# **1. Executive Summary**

Sovera OWM is the organizational intelligence layer for enterprise AI.

AI systems can retrieve information, generate language, query databases, and execute tools. They do not automatically understand how an organization defines its customers, applies its policies, assigns authority, interprets exceptions, or makes decisions.

**OWM provides that understanding.**

OWM maintains a machine-interpretable representation of the organization:

* entities
* relationships
* concepts
* processes
* policies
* roles and authority
* events and decisions
* exceptions
* evidence
* provenance
* temporal state
* semantic mappings
* organizational context
Sovera is an **agentic enterprise platform**, but it does not build a proprietary agent runtime.

Instead, Sovera uses **Agno as the agent execution and orchestration runtime**, while retaining ownership of the differentiated enterprise substrate:

**OWM tells agents how the organization works.** **The agent runtime lets them reason and act.** **Sovera governance controls what they are allowed to do.**

This separation prevents Sovera from spending engineering resources recreating commodity agent-runtime infrastructure while keeping the organizational intelligence layer, identity, governance, observability, evaluation, and decision capabilities proprietary.

---

# **2. Product Thesis**

**AI knows what is in your data. It does not automatically know what it means.**

Enterprise AI requires more than access to enterprise information.

It requires organizational understanding.

Models provide intelligence.

Enterprise systems provide information and capabilities.

**OWM provides organizational understanding.**

The architectural progression is:

**Enterprise Information → Evidence → Organizational Understanding → Decision → Action**

OWM is the semantic and organizational layer between enterprise information and AI execution.

---

# **3. Product Positioning**

Sovera is an **agentic enterprise intelligence platform powered by an Organizational World Model.**

OWM is the platform’s organizational intelligence kernel.

The platform provides:

* organizational understanding
* agent execution
* decision intelligence
* governed action
* enterprise AI experiences
The product should not be positioned as:

* another RAG platform
* another knowledge graph
* another enterprise search engine
* another ontology platform
* another agent framework
* another workflow engine
Instead:

**Sovera teaches AI how your organization works and gives agents the ability to act on that understanding.**

---

# **4. Architectural Principle**

## **OWM is not the agent runtime.**

OWM is the organizational understanding substrate used by the agent runtime.

The agent runtime is responsible for:

* execution
* orchestration
* tool invocation
* workflow control
* agent coordination
* runtime state
* execution loops
* retries
* human interaction during execution
Sovera is responsible for:

* organizational meaning
* organizational context
* identity
* authority
* policies
* evidence
* provenance
* temporal state
* decisions
* governance
* observability
* evaluation
* organizational learning
Agno provides the runtime implementation for agentic execution.

---

# **5. Core Conceptual Model**

The OWM model remains based on five conceptual layers.

## **5.1 Evidence**

What the organization has.

Examples:

* documents
* databases
* emails
* SaaS systems
* contracts
* policies
* tickets
* spreadsheets
* APIs
* operational records
Evidence is the grounding substrate.

---

## **5.2 Knowledge**

What the organization knows.

Examples:

* entities
* facts
* relationships
* attributes
* events
* evidence references
* provenance
* confidence
---

## **5.3 Meaning**

What information means within the organization.

Examples:

* concepts
* ontology
* semantic mappings
* definitions
* constraints
* policies
* processes
* roles
* authority
* business rules
---

## **5.4 Time**

When something was true, recorded, changed, or believed.

OWM must distinguish:

* valid/world time
* recording/system time
* historical organizational state
* policy validity
* role validity
* decision validity
---

## **5.5 Intelligence**

What the organization can do with its understanding.

Examples:

* answer questions
* retrieve context
* reason
* make decisions
* operate agents
* execute workflows
* govern actions
* audit decisions
* learn from outcomes
Intelligence is enabled by OWM but is not synonymous with OWM.

---

# **6. System Architecture**

The canonical architecture is:

```
┌─────────────────────────────────────────────────────────┐
│                  SOVERA EXPERIENCES                     │
│ Agents · Copilots · AI-Native BI · Search · Automation │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                 AGENTIC EXECUTION LAYER                │
│                         AGNO                            │
│                                                         │
│ Agents · Teams · Workflows · Tool Calls · MCP · A2A    │
│ Execution · Routing · State · HITL · Background Runs   │
└───────────────────────────┬─────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
┌─────────────▼─────────────┐   ┌─────────▼──────────────┐
│       SOVERA OWM          │   │   DECISION INTELLIGENCE│
│                           │   │                        │
│ Evidence                  │   │ Decision Questions    │
│ Knowledge                 │   │ Typed Outcomes        │
│ Meaning                   │   │ Confidence             │
│ Time                      │   │ Evaluation             │
│ Context                   │   │ Decision Records       │
│ Policies                  │   │ Governance             │
│ Authority                 │   │                        │
└─────────────┬─────────────┘   └─────────┬──────────────┘
              │                           │
              └─────────────┬─────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│           ENTERPRISE INFORMATION & CAPABILITIES        │
│ CRM · ERP · SaaS · Databases · Documents · APIs · MCP  │
└─────────────────────────────────────────────────────────┘
```

Cross-cutting Sovera capabilities:

* Identity
* Authorization
* Observability
* Evaluation
* Audit
* Governance
---

# **7. Scope Boundary**

## **7.1 Sovera owns**

### **Organizational Understanding**

* OWM semantic state
* organizational ontology
* entities
* relationships
* concepts
* semantic mappings
* processes
* policies
* roles
* authority
* exceptions
* decisions
* evidence
* provenance
* temporal state
* context assembly
### **Agent Integration**

* OWM context exposed to agents
* agent identity integration
* organizational authorization
* policy enforcement
* decision integration
* action governance
* agent observability
* agent evaluation
* organizational learning from agent outcomes
### **Decision Intelligence**

* decision question
* candidate outcomes
* decision context
* decision engine abstraction
* confidence
* evidence
* decision records
* decision replay
* governance outcomes
---

## **7.2 Agno owns**

Agno is used as the execution substrate for:

* agent execution loops
* agent definitions
* teams
* workflows
* orchestration
* tool invocation
* runtime state
* execution routing
* retries
* MCP integration
* A2A integration
* human-in-the-loop execution primitives
* background execution
Sovera should integrate with these capabilities rather than recreate them.

---

## **7.3 Explicitly out of scope**

Sovera will not build a proprietary:

* general-purpose agent runtime
* agent execution loop
* workflow engine
* generic agent session system
* generic agent memory system
* generic tool orchestration framework
* agent transport protocol
* replacement for MCP
* replacement for A2A
* general-purpose agent control plane
These capabilities may be exposed through Sovera APIs, but their underlying runtime implementation is delegated to Agno or other appropriate infrastructure.

---

# **8. OWM Domain Model**

The OWM core consists of the following primitives.

## **8.1 Entity**

A real or organizationally meaningful thing.

Examples:

* customer
* account
* employee
* product
* supplier
* contract
* location
---

## **8.2 Relationship**

A meaningful relationship between entities.

Examples:

* customer owns account
* employee manages account
* contract governs customer
* employee reports to manager
---

## **8.3 Concept**

An organizational abstraction or semantic category.

Examples:

* strategic account
* enterprise customer
* qualified opportunity
* high-risk transaction
---

## **8.4 Attribute**

A property associated with an entity or concept.

---

## **8.5 Event**

Something that happened or changed organizational state.

---

## **8.6 Process**

An organizational procedure or workflow.

---

## **8.7 Policy**

A rule or governing statement that determines what is permitted, required, or prohibited.

---

## **8.8 Role and Authority**

Representation of:

* organizational roles
* responsibility
* authority
* delegation
* approval thresholds
* ownership
---

## **8.9 Decision**

A recorded organizational judgment.

A decision contains:

* question
* subject
* context
* applicable policies
* authority
* evidence
* candidate outcomes
* result
* confidence
* decision maker
* timestamp
* validity
* resulting action
---

## **8.10 Exception**

A deviation from the normal organizational rule or process.

Exceptions are first-class because enterprise decisions frequently depend on them.

---

## **8.11 Evidence**

Evidence supporting an organizational assertion, interpretation, or decision.

Evidence must remain distinguishable from the semantic state derived from it.

---

## **8.12 Semantic Mapping**

A mapping between an external system concept and an OWM concept.

Example:

```
CRM.Account
ERP.Customer
Support.Client
Contract.Counterparty
        ↓
OWM.Customer
```

The source systems retain their own terminology.

OWM establishes organizational meaning across those systems.

---

# **9. Evidence and Understanding Lifecycle**

The fundamental lifecycle remains:

```
Enterprise Information
        ↓
Evidence
        ↓
Extraction / Interpretation
        ↓
Proposal
        ↓
Validation
        ↓
Resolution
        ↓
Promotion
        ↓
OWM Semantic State
        ↓
Context
        ↓
Decision / Agent Execution
        ↓
Action / Outcome
        ↓
New Evidence
```

Extraction must not silently write semantic truth into OWM.

Machine-generated interpretations become proposals supported by evidence and subject to the appropriate validation and governance process.

---

# **10. Organizational Context**

The primary interface between OWM and the agent runtime is **organizational context**.

An agent should not need to understand the internal OWM graph representation.

Instead, OWM assembles a context appropriate to:

* agent identity
* user identity
* task
* semantic intent
* entities
* concepts
* policies
* processes
* authority
* temporal state
* evidence
* permissions
* organizational scope
The resulting context becomes an input to the agent runtime.

---

# **11. Agent Runtime Integration**

Agno is treated as an implementation layer behind a Sovera abstraction.

The desired dependency direction is:

```
Sovera Application
       ↓
Sovera Agent Abstraction
       ↓
Agno Adapter
       ↓
Agno Runtime
```

Sovera should not allow Agno-specific concepts to leak unnecessarily into the OWM domain model.

This preserves the option to replace Agno in the future.

---

# **12. Agent Context**

The agent runtime receives context assembled by Sovera.

Conceptually:

```
Agent Goal
    ↓
Semantic Intent
    ↓
OWM Context Assembly
    ↓
Organizational Context
    ↓
Agno Agent
    ↓
Reason / Tool / Observe / Continue
```

The OWM context may include:

* relevant entities
* organizational definitions
* relationships
* policies
* processes
* authority
* historical state
* evidence
* exceptions
* prior decisions
* confidence
* constraints
OWM remains authoritative for organizational understanding.

---

# **13. Agent Identity**

Agent identity remains a Sovera concern.

Every meaningful agent action must be attributable to:

* human initiator
* organizational identity
* agent identity
* execution/run
* capability/tool
* action
* resulting outcome
Agno runtime identifiers may be mapped into Sovera identity and execution records but do not become the authoritative organizational identity system.

---

# **14. Capability and Tool Integration**

Agents require access to enterprise capabilities.

Sovera should expose these through a governed capability layer.

Capabilities may be implemented through:

* MCP
* REST
* APIs
* SDKs
* Python functions
* database tools
* enterprise connectors
* A2A
Each capability should have metadata describing, where applicable:

* capability name
* description
* input schema
* output schema
* identity requirements
* authorization requirements
* side effects
* risk level
* approval requirements
* applicable policies
Agno is responsible for invoking the capability.

Sovera is responsible for determining whether the agent is authorized to use it and under what constraints.

---

# **15. Governance**

Agent execution must remain subordinate to organizational governance.

The canonical flow is:

```
Agent Intent
     ↓
OWM Context
     ↓
Decision
     ↓
Governance Gate
     ↓
Authorized Action
     ↓
Enterprise System
```

Possible governance outcomes include:

* ACT
* ROUTE
* ESCALATE
* REQUEST_EVIDENCE
* REJECT
* HUMAN_REVIEW
The agent runtime must not bypass the governance layer for governed actions.

---

# **16. Decision Intelligence**

Decision-making remains a first-class Sovera capability.

The Decision Engine is provider-neutral.

Possible implementations include:

* deterministic rules
* LLM decisioning
* TypeSafe / typed decision models
* specialized models
* human decision makers
* composite decision engines
The interface conceptually remains:

```
DecisionEngine.decide(
    question,
    context,
    candidate_outcomes
)
```

The engine returns structured decision results rather than relying exclusively on natural-language reasoning.

---

# **17. Decision Record**

Every governed decision should be reconstructable.

A Decision Record includes:

* decision question
* subject
* organizational context
* applicable policies
* evidence
* authority
* candidate outcomes
* selected outcome
* confidence
* decision engine
* decision timestamp
* OWM state
* resulting action
* outcome
This enables historical decision replay.

---

# **18. Agent Observability**

Sovera already provides observability and remains the canonical system for agent observability.

The runtime should emit execution telemetry sufficient to reconstruct:

* agent run
* goal
* model calls
* tool calls
* OWM context
* decisions
* approvals
* failures
* latency
* cost
* outcome
Agno instrumentation can feed the Sovera observability substrate.

Agno telemetry should not become a parallel source of truth.

---

# **19. Agent Evaluation**

Sovera already provides evaluation infrastructure.

Agent evaluations should extend beyond generic model quality.

Evaluation dimensions may include:

### **Organizational understanding**

Did the agent correctly interpret the organization’s terminology?

### **Context selection**

Did the agent retrieve the appropriate organizational context?

### **Policy application**

Did the agent identify and apply the correct policy?

### **Authority**

Did the agent correctly determine who could authorize the action?

### **Decision quality**

Was the decision appropriate given the available organizational state?

### **Execution**

Did the agent perform the correct action?

### **Governance**

Did the agent respect organizational constraints?

### **Outcome**

Did the resulting action achieve the intended result?

This becomes an important differentiator from generic agent evaluation platforms.

---

# **20. Organizational Learning**

Agent activity should not disappear into execution logs.

The learning loop is:

```
Agent Execution
      ↓
Observation
      ↓
Outcome
      ↓
Evidence
      ↓
Proposal
      ↓
Validation / Review
      ↓
OWM
```

Examples:

* human correction of an agent interpretation
* newly discovered organizational exception
* changed policy
* recurring agent failure
* newly observed relationship
* outcome contradicting an existing assumption
Agent execution therefore becomes another source of organizational evidence.

Agents can help teach the OWM, but agents must not silently rewrite organizational truth.

---

# **21. Agent Memory Boundary**

Sovera should distinguish three different concepts.

### **Working Memory**

Runtime state required for the current execution.

**Agno/runtime responsibility.**

### **Episodic Execution Memory**

Information about previous agent runs and interactions.

**Sovera observability/execution infrastructure, with runtime support as appropriate.**

### **Organizational Memory**

The durable representation of how the organization works.

**OWM responsibility.**

The system must not collapse these into one generic concept called “memory.”

---

# **22. Agentic Execution Model**

A canonical execution looks like:

```
User Request
     ↓
Sovera Identity
     ↓
Semantic Intent
     ↓
OWM Context Assembly
     ↓
Agno Agent
     ↓
Reason
     ↓
Tool / Capability
     ↓
Observation
     ↓
OWM / Decision Engine
     ↓
Reason / Replan
     ↓
Governance Gate
     ↓
Authorized Action
     ↓
Outcome
     ↓
Sovera Observability
     ↓
Potential Organizational Learning
```

This is the core agentic architecture for Sovera.

---

# **23. Canonical Example: Acme 15% Discount**

User asks:

“Can we give Acme a 15% discount?”

The agent does not simply retrieve a pricing document.

### **OWM establishes:**

* Acme is a customer.
* Acme is a strategic account.
* Acme has a specific pricing tier.
* The current pricing policy permits certain discounts.
* Acme’s contract contains an exception.
* The exception has a validity period.
* A specific organizational role has approval authority.
* The requesting user has a particular organizational identity and authority.
### **Agno executes:**

1. identify the customer
2. obtain relevant organizational context
3. retrieve supporting information
4. invoke decision capability
5. determine next execution step
6. request approval if required
7. execute the authorized action

⠀
### **Sovera governance determines:**

15% is permitted under the applicable contract exception, but requires VP Sales approval.

The resulting approval request, decision, action, and outcome are recorded.

---

# **24. Agent Experiences**

The architecture supports multiple experiences on the same OWM:

* AI agents
* copilots
* enterprise search
* AI-native BI
* decision intelligence
* workflow automation
* customer service
* sales intelligence
* operations
* internal knowledge applications
The objective is:

**One organizational world model. Many intelligence experiences.**

---

# **25. MCP and A2A**

Sovera should use established interoperability protocols rather than recreate them.

### **MCP**

Used for exposing enterprise capabilities and tools to agents.

### **A2A**

Used where agent-to-agent interoperability is required.

Agno may provide runtime support for these protocols.

Sovera remains responsible for:

* organizational context
* identity
* authorization
* governance
* policy
* audit
* organizational semantics
---

# **26. Functional Requirements**

## **FR-1 OWM Semantic State**

The system shall maintain organizational semantic state representing entities, relationships, concepts, policies, processes, roles, authority, decisions, exceptions, evidence, provenance, mappings, and temporal state.

## **FR-2 Evidence**

The system shall preserve evidence supporting organizational assertions.

## **FR-3 Provenance**

The system shall maintain provenance linking semantic state to supporting evidence and source systems.

## **FR-4 Temporal State**

The system shall support historical organizational state and temporal validity.

## **FR-5 Semantic Mapping**

The system shall reconcile heterogeneous source-system terminology into OWM concepts.

## **FR-6 Context Assembly**

The system shall assemble organizational context for agents, questions, decisions, and applications.

## **FR-7 Agent Runtime**

The system shall integrate with Agno for agent and workflow execution.

## **FR-8 Agent Identity**

The system shall associate agent execution with authenticated organizational identities.

## **FR-9 Capability Governance**

The system shall govern access to enterprise capabilities based on identity, authority, policy, and risk.

## **FR-10 Decision Engine**

The system shall provide a provider-neutral decision engine interface.

## **FR-11 Governance Gate**

The system shall enforce organizational governance before governed actions are executed.

## **FR-12 Observability**

The system shall record agent execution, tool calls, decisions, actions, failures, and outcomes.

## **FR-13 Evaluation**

The system shall evaluate agent behavior against organizational understanding, policy, decision, execution, and outcome criteria.

## **FR-14 Learning**

The system shall support promotion of validated agent observations and outcomes into OWM.

## **FR-15 Audit**

The system shall maintain sufficient records to reconstruct significant decisions and actions.

---

# **27. Non-Functional Requirements**

The platform should support:

* enterprise security
* multi-tenancy
* fine-grained authorization
* auditability
* temporal correctness
* provenance
* observability
* evaluation
* extensibility
* vendor independence at the domain layer
* replaceable agent runtime
* API-first integration
* MCP interoperability
* A2A interoperability
* reliable execution through the selected runtime
* deployment in enterprise environments
---

# **28. Architectural Dependency Rules**

The following dependency direction should be preserved.

```
Application
    ↓
Agent Abstraction
    ↓
Runtime Adapter
    ↓
Agno
```

And:

```
Agent Runtime
    ↓
Sovera Interfaces
    ↓
OWM
```

The OWM domain must not depend directly on:

* Agno
* OpenAI
* Anthropic
* TypeSafe
* Neo4j
* PostgreSQL
* MCP implementation details
* specific document extraction libraries
These belong behind adapters or ports.

---

# **29. What Is Differentiated**

Sovera’s differentiation is not the ability to run an agent.

Agents are increasingly commodity infrastructure.

The differentiated asset is:

**A continuously enriched machine-interpretable model of how an organization works.**

The moat compounds through:

* organizational definitions
* semantic mappings
* entity resolution
* policies
* exceptions
* processes
* authority
* historical state
* decisions
* evidence
* outcomes
* corrections
* learned organizational behavior
The longer an organization uses OWM, the richer its organizational understanding becomes.

---

# **30. Strategic Architecture**

The strategic stack is:

```
AI EXPERIENCES
                   │
                   ▼
         AGENTIC EXECUTION
                AGNO
                   │
                   ▼
        ┌───────────────────┐
        │        OWM        │
        │                   │
        │ Organizational    │
        │ Understanding     │
        └───────────────────┘
                   │
                   ▼
          ENTERPRISE WORLD
```

Or more simply:

**Agno runs the agent.** **OWM tells it how the organization works.** **Sovera governs what it can do.**

---

# **31. Release Strategy**

The previous release structure is simplified because agent-runtime infrastructure is no longer a Sovera build objective.

## **Release A — Evidence Substrate**

* source ingestion
* evidence
* provenance
* extraction proposals
* validation
* promotion
## **Release B — Semantic Understanding**

* ontology
* concepts
* entity resolution
* semantic mappings
* organizational definitions
## **Release C — Temporal OWM**

* temporal state
* historical truth
* policy validity
* role/authority validity
* historical replay
## **Release D — Organizational Context**

* semantic intent
* context assembly
* policy context
* authority context
* evidence grounding
## **Release E — Decision Intelligence**

* decision engine
* typed decisions
* confidence
* decision records
* governance gates
## **Release F — Agentic Execution**

* Agno integration
* agent abstraction
* OWM context injection
* governed tools
* identity integration
* agent observability
* agent evaluation
## **Release G — Organizational Learning**

* agent observations
* outcome capture
* proposals
* human corrections
* validated promotion
* continuous enrichment
---

# **32. Success Metrics**

The product should ultimately measure organizational understanding rather than agent activity alone.

Potential metrics include:

### **Organizational Coverage**

How much of the organization’s relevant concepts, entities, policies, processes, and relationships are represented?

### **Semantic Accuracy**

How accurately does OWM represent organizational meaning?

### **Context Accuracy**

How often does the system provide the correct organizational context?

### **Decision Accuracy**

How often do decisions align with documented organizational policy and authority?

### **Grounded Action Rate**

How often can agents complete tasks using evidence-backed organizational context?

### **Governance Compliance**

How often do agent actions comply with organizational policy and authority?

### **Learning Rate**

How quickly does validated new organizational knowledge become part of OWM?

### **Reuse**

How many AI experiences and agents consume the same OWM?

---

# **33. Key Product Principle**

The platform should optimize for:

**How much of an organization’s meaning can AI reliably understand, reason about, and act upon?**

Not:

How many agents can we run?

Not:

How many tools can we connect?

Not:

How many documents can we retrieve?

The agent runtime is infrastructure.

**Organizational understanding is the product.**

---

# **34. Final Product Thesis**

Sovera is building the organizational intelligence layer for agentic AI.

Enterprise systems contain information.

Models provide intelligence.

Agent runtimes provide execution.

**OWM provides organizational understanding.**

That understanding connects:

**Evidence → Meaning → Context → Decision → Action → Outcome → Learning**

The result is an AI platform that does not merely give agents access to enterprise systems.

It gives them an understanding of **how the enterprise works**.

**Teach AI how your company works.** **Once.** **Then let every agent build on it.**

---

# **35. Supersession Note**

This document supersedes the previous Sovera OWM PRD with respect to agent-platform architecture and scope.

The following previous direction is explicitly superseded:

Sovera should build a proprietary agent runtime and orchestration infrastructure.

The new direction is:

**Sovera owns the Organizational World Model and differentiated enterprise intelligence substrate. Agno provides the agent execution runtime.**

Existing OWM, identity, observability, and evaluation implementations remain part of the Sovera platform and become the authoritative substrate surrounding the runtime.

The architectural objective is therefore not to build an agent platform from first principles.

It is to build the **organizational intelligence platform that makes agentic execution enterprise-aware, governable, explainable, and continuously improving.**