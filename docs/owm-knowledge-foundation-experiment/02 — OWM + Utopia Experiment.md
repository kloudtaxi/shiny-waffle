## 02 — OWM + Utopia Experiment 

Exactly. Since Utopia is already running, I would **not start by generating 50 documents and CSVs**. Start with the *organizational model and decision scenarios*, then generate the minimum evidence corpus that causes Utopia to construct that model.

Utopia is particularly useful for this experiment because it can ingest Markdown/CSV and other common formats, extract entities/facts against an ontology, resolve entities, retain provenance and temporal validity, and expose graph/search/SQL capabilities.

## **1. Start with the decisions, not the data**

I’d make **five demo questions** the backbone:

|  **Scenario**  |  **Question**  |  **What it teaches us**  | 
|---|---|---|
|  1  |  Can Sarah approve Acme’s 15% discount?  |  Authority + policy + relationship  |
|  2  |  Can we offer Acme 18%?  |  Exception + constraint  |
|  3  |  Could Sarah have approved 15% last year?  |  Temporal organizational state  |
|  4  |  Why is Acme eligible for 15%?  |  Evidence + provenance  |
|  5  |  What happens if the contract is missing?  |  Uncertainty + evidence requirements  |
These become your **acceptance tests for OWM**.

---

# **2. Define the OWM before creating the corpus**

Create a simple `owm-spec.md` that is *your* conceptual model, independent of Utopia.

For example:

```
Organization
Person
Employee
Role
Department
Customer
Account
Product
Contract
Policy
Exception
Order
DiscountRequest
Approval
Decision
```

Then relationships:

```
Employee OWNS Account
Employee REPORTS_TO Employee
Employee HAS_ROLE Role
Account REPRESENTS Customer
Customer HAS_CONTRACT Contract
Contract COVERS Product
Customer ELIGIBLE_FOR Exception
DiscountRequest REQUESTS Discount
DiscountRequest FOR Customer
DiscountRequest FOR Product
DiscountRequest SUBMITTED_BY Employee
Policy GOVERNS DiscountRequest
Role GRANTS_AUTHORITY Approval
Approval AUTHORIZES DiscountRequest
Decision EVALUATES DiscountRequest
Decision SUPPORTED_BY Evidence
```

Don’t obsess over getting this perfect.

**The point is to discover the model.**

---

# **3. Then create the “ground truth”**

This is the most important file in the whole exercise.

Create:

```
ground_truth/
    organization.yaml
    entities.yaml
    relationships.yaml
    policies.yaml
    temporal_facts.yaml
    decisions.yaml
```

For example:

```
customer:
  id: CUST-1001
  canonical_name: Acme Manufacturing
  aliases:
    - Acme
    - Acme Mfg. Holdings
    - ACME Manufacturing

account:
  id: CRM-2048
  customer: CUST-1001
  owner: EMP-101
  segment: Strategic
```

And:

```
authority:
  - person: EMP-101
    action: approve_discount
    maximum: 0.10

  - person: EMP-200
    action: approve_discount
    minimum: 0.10
    maximum: 0.20

  - person: EMP-300
    action: approve_discount
    minimum: 0.20
```

This is **not what you feed the client**.

It’s your laboratory control.

You need to know what the answer *should* be before asking Utopia/OWM to derive it.

---

# **4. Now manufacture the evidence**

This is where the dataset becomes interesting.

Create approximately **10–15 pieces of evidence**, not hundreds.

### **Structured**

```
structured/
    customers.csv
    crm_accounts.csv
    employees.csv
    products.csv
    erp_orders.csv
    discount_requests.csv
```

### **Documents**

```
documents/
    pricing_policy_2025.md
    pricing_policy_2026.md
    approval_authority_matrix.md
    organization_chart.md
    acme_master_supply_agreement.md
    acme_pricing_exception.md
    sales_discount_sop.md
    acme_account_strategy.md
    email_sarah_to_michael.md
```

The trick is that **no single artifact contains the answer**.

---

# **5. Deliberately introduce ambiguity**

This is where the dataset becomes an OWM experiment rather than a RAG benchmark.

For example:

### **Identity ambiguity**

```
CRM
CRM-2048 → Acme Manufacturing

ERP
C-1001 → Acme Mfg. Holdings

Contract
ACME-MFG-2025 → Acme Manufacturing
```

Utopia should resolve these into one organization.

---

### **Temporal ambiguity**

2025:

```
AE approval limit = 15%
```

2026:

```
AE approval limit = 10%
VP Sales = >10% and <=20%
```

Now ask:

Could Sarah approve 15%?

The answer depends on **when**.

That’s a beautiful demonstration of why an evergreen organizational model needs time.

---

### **Policy vs exception**

Contract:

```
Acme may receive up to 15%
```

Authority policy:

```
Sarah may approve up to 10%
Michael may approve up to 20%
```

This creates the critical distinction:

**Eligibility is not authority.**

That is an OWM concept.

---

### **Organizational relationship**

Don’t put:

```
Michael can approve Acme discounts.
```

in a document.

Instead distribute the facts:

```
Sarah → owns Acme
Sarah → reports to Michael
Michael → VP Sales
VP Sales → has approval authority >10% ≤20%
```

Now the model has to **compose organizational meaning**.

---

# **6. Feed the evidence into Utopia**

This is where your existing installation becomes the knowledge foundation.

I’d create a dedicated knowledge base:

```
Northstar Industrial Systems
```

Then load:

```
CSV
 ↓
Utopia structured knowledge

Markdown
 ↓
Utopia document knowledge

Ontology
 ↓
Utopia semantic structure
```

Utopia’s extraction process follows the ontology and attaches provenance and temporal information to extracted facts; entity resolution also explicitly handles aliases/duplicates and uncertain cases.

**Don’t immediately build the Sovera UI.**

First get the underlying knowledge base right.

---

# **7. Watch what Utopia gets wrong**

This is actually one of the most valuable parts of the exercise.

Create a simple evaluation sheet:

|  **Fact**  |  **Ground truth**  |  **Utopia**  |  **OWM needed?**  | 
|---|---|---|---|
|  CRM-2048 = Acme  |  ✓  |  ?  |  |
|  C-1001 = Acme  |  ✓  |  ?  |  |
|  Sarah owns Acme  |  ✓  |  ?  |  |
|  Sarah max authority = 10%  |  ✓  |  ?  |  |
|  Michael max authority = 20%  |  ✓  |  ?  |  |
|  Acme exception = 15%  |  ✓  |  ?  |  |
|  Exception expires 2028  |  ✓  |  ?  |  |
|  15% requires VP  |  ✓  |  ?  |  |
|  Sarah can approve 15%  |  **NO**  |  ?  |  **YES**  | 
The last column is important.

Whenever you discover:

“Utopia knows X and Y, but it doesn’t naturally understand the organizational implication X + Y → Z”

**that’s a candidate OWM capability.**

---

# **8. Then build the OWM layer**

Only after you’ve done that should you create:

```
owm/
    domain-model/
    ontology/
    policies/
    authority/
    decisions/
    context/
```

And your first OWM object could conceptually be:

```
{
  "decision": "DR-9001",
  "subject": "Acme Manufacturing",
  "action": "approve_discount",
  "requested_value": 0.15,
  "product": "NS-500",
  "requestor": "Sarah Chen",
  "commercial_eligibility": true,
  "requestor_authority": false,
  "required_authority": "VP_SALES",
  "authorized_approver": "Michael Torres",
  "decision": "APPROVE_WITH_AUTHORIZATION",
  "evidence": [
    "MSA-ACME-2025",
    "pricing_policy_2026",
    "approval_authority_matrix",
    "organization_chart",
    "discount_request"
  ]
}
```

Notice what happened.

**Utopia didn’t disappear.**

It provides the knowledge required to construct this.

OWM gives that knowledge **organizational semantics and decision structure**.

---

# **9. The most important experiment**

Once scenario #1 works, start removing pieces.

### **Experiment A**

Remove the org chart.

Can the system determine who has authority?

### **Experiment B**

Remove the pricing exception.

Can it determine Acme’s 15% eligibility?

### **Experiment C**

Change the date.

Does the answer change?

### **Experiment D**

Change 15% → 18%.

Does the decision change?

### **Experiment E**

Change product NS-500 → NS-Cloud.

Does the contract exception still apply?

### **Experiment F**

Create another customer with a similar name.

Does entity resolution remain correct?

These are effectively **unit tests for organizational understanding**.

---

# **10. The dataset structure I’d use**

I’d create this repository:

```
northstar-owm-lab/

├── README.md
│
├── owm/
│   ├── domain-model.yaml
│   ├── ontology.yaml
│   ├── policies.yaml
│   ├── authority.yaml
│   └── decisions.yaml
│
├── evidence/
│   ├── structured/
│   │   ├── customers.csv
│   │   ├── crm_accounts.csv
│   │   ├── employees.csv
│   │   ├── products.csv
│   │   ├── erp_orders.csv
│   │   └── discount_requests.csv
│   │
│   └── documents/
│       ├── pricing_policy_2025.md
│       ├── pricing_policy_2026.md
│       ├── approval_authority_matrix.md
│       ├── organization_chart.md
│       ├── acme_master_supply_agreement.md
│       ├── acme_pricing_exception.md
│       ├── sales_discount_sop.md
│       ├── acme_account_strategy.md
│       └── email_sarah_to_michael.md
│
├── ground-truth/
│   ├── entities.yaml
│   ├── relationships.yaml
│   ├── temporal-facts.yaml
│   └── expected-decisions.yaml
│
└── scenarios/
    ├── 01-standard-discount.yaml
    ├── 02-exceeds-exception.yaml
    ├── 03-historical-policy.yaml
    ├── 04-missing-evidence.yaml
    └── 05-conflicting-information.yaml
```

### **And I’d make one design rule explicit:**

**Evidence is messy. Ground truth is clean. OWM is the continuously evolving model that sits between them.**

That gives us a very clean experimental loop:

```
EVIDENCE
                 │
                 ▼
        ┌─────────────────┐
        │ UTOPIA / OG-RAG │
        │                 │
        │ knowledge       │
        │ extraction      │
        │ entity resolution
        │ provenance      │
        │ temporal facts  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │       OWM       │
        │                 │
        │ domain model    │
        │ ontology        │
        │ context         │
        │ authority       │
        │ policies        │
        │ decisions       │
        └────────┬────────┘
                 │
                 ▼
             DECISION
```

**That’s the experiment I’d run before writing a line of demo UI.**

And because you already have Utopia locally, we can make this very concrete: **next I would build the Northstar dataset itself, starting with the OWM specification + ground truth, then generate the 15-ish evidence artifacts around it.** That gives you something you can immediately load into your existing Utopia instance and begin discovering where the boundary between **knowledge foundation** and **OWM** actually lies.