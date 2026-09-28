## 03 — OWM Domain Model + Ground Truth 

# **Northstar Industrial Systems**

## **Organizational Ground Truth — OWM Demo v0.1**

### **Purpose**

This document defines the canonical organizational truth for the Northstar Industrial Systems synthetic enterprise used in the Sovera OWM demonstration.

It is the reference model against which the knowledge foundation and OWM implementation are evaluated.

The evidence corpus intentionally contains fragmented, duplicated, differently named, historical, and partially conflicting representations of these facts. The ground truth represents the intended organizational reality after those representations are reconciled.

---

# **1. Organization**

**Canonical organization**

* Name: Northstar Industrial Systems
* Organization ID: ORG-001
* Industry: Industrial equipment and software
* Headquarters: Chicago, Illinois
* Employees: approximately 850
* Annual revenue: approximately $240M
* Operating model: direct enterprise sales
* Primary demonstration systems:

  * Northstar CRM
  * Northstar ERP
  * Northstar Service
  * Northstar Drive
---

# **2. Canonical Entities**

## **2.1 Customers**

### **Acme Manufacturing**

* Customer ID: CUST-1001
* Canonical name: Acme Manufacturing
* Customer type: Enterprise
* Industry: Industrial Manufacturing
* Approximate annual revenue: $125M
* Strategic account: Yes
Known aliases:

* Acme
* Acme Manufacturing
* Acme Mfg. Holdings
* ACME Manufacturing
* ACME-MFG-2025
Source-system identifiers:

* CRM account: CRM-2048
* ERP customer: C-1001
* Master supply agreement: MSA-ACME-2025
**Identity rule**

CRM-2048, C-1001, and ACME-MFG-2025 refer to the same real-world customer: Acme Manufacturing.

---

### **BlueRiver Logistics**

* Customer ID: CUST-1002
* Canonical name: BlueRiver Logistics
* Customer type: Enterprise
* Industry: Logistics
* Strategic account: No
---

### **Cedar Health Systems**

* Customer ID: CUST-1003
* Canonical name: Cedar Health Systems
* Customer type: Enterprise
* Industry: Healthcare
* Strategic account: No
---

# **3. Employees**

## **Sarah Chen**

* Employee ID: EMP-101
* Name: Sarah Chen
* Title: Enterprise Account Executive
* Department: Sales
* Manager: EMP-200
* Primary responsibility: enterprise customer accounts
* Account ownership: Acme Manufacturing
### **Sarah’s authority**

For the 2026 pricing policy:

* May approve discounts up to and including 10%.
* May not independently approve discounts greater than 10%.
* Must route discounts greater than 10% to the appropriate approval authority.
---

## **Michael Torres**

* Employee ID: EMP-200
* Name: Michael Torres
* Title: VP Sales
* Department: Sales
* Manager: EMP-300
### **Michael’s authority**

For the 2026 pricing policy:

* May approve discounts greater than 10%.
* May approve discounts up to and including 20%.
* Is the designated approval authority for Sarah’s 15% Acme discount request.
---

## **David Morgan**

* Employee ID: EMP-300
* Name: David Morgan
* Title: Chief Revenue Officer
* Department: Executive
* Manager: None
### **David’s authority**

For the 2026 pricing policy:

* Required approval authority for discounts greater than 20%.
---

## **Priya Shah**

* Employee ID: EMP-401
* Name: Priya Shah
* Title: Finance Manager
* Department: Finance
* Manager: EMP-402
Priya is not the approval authority for sales discounts in the demonstration scenarios.

---

# **4. Organizational Relationships**

The following relationships are canonical.

```
Sarah Chen
    ├── employee_of → Northstar Industrial Systems
    ├── member_of → Sales
    ├── has_role → Enterprise Account Executive
    ├── reports_to → Michael Torres
    └── owns → Acme Manufacturing

Michael Torres
    ├── employee_of → Northstar Industrial Systems
    ├── member_of → Sales
    ├── has_role → VP Sales
    ├── reports_to → David Morgan
    └── has_authority → Enterprise Discount Approval >10% and ≤20%

David Morgan
    ├── employee_of → Northstar Industrial Systems
    ├── has_role → Chief Revenue Officer
    └── has_authority → Enterprise Discount Approval >20%
```

---

# **5. Products**

## **NS-500 Industrial Controller**

* Product ID: PROD-001
* Name: NS-500 Industrial Controller
* Category: Equipment
* Current list price: $250,000
## **NS-Cloud Operations Suite**

* Product ID: PROD-002
* Name: NS-Cloud Operations Suite
* Category: Software
* Current list price: $120,000
## **NS-Edge Monitoring Package**

* Product ID: PROD-003
* Name: NS-Edge Monitoring Package
* Category: Software
* Current list price: $85,000
---

# **6. Customer / Account Relationships**

Acme Manufacturing is:

* a Northstar customer;
* an enterprise customer;
* a strategic account;
* owned by Sarah Chen;
* assigned to the Midwest Enterprise segment;
* eligible for a contractual pricing exception on the NS-500 Industrial Controller.
CRM account:

* CRM-2048
ERP customer:

* C-1001
The different identifiers do not represent different customers.

---

# **7. Contracts**

## **Acme Master Supply Agreement**

* Contract ID: MSA-ACME-2025
* Customer: Acme Manufacturing
* Effective: 2025-04-01
* Expiration: 2028-03-31
* Status on 2026-09-23: Active
### **Pricing provision**

Acme is eligible for discounts of up to **15%** on NS-500 Industrial Controllers.

The contractual pricing eligibility does **not** modify Northstar’s internal approval authority.

Therefore:

```
Contractual eligibility
        ≠
Internal approval authority
```

A Northstar employee must still have the appropriate internal authority to approve the requested discount.

---

# **8. Pricing Exception**

## **Acme NS-500 Strategic Account Exception**

* Exception ID: EXC-ACME-NS500-15
* Customer: Acme Manufacturing
* Product: NS-500 Industrial Controller
* Maximum eligible discount: 15%
* Effective: 2025-04-01
* Expiration: 2028-03-31
* Status on 2026-09-23: Active
The exception establishes commercial eligibility.

It does not grant additional approval authority to Sarah Chen or any other employee.

---

# **9. Pricing Policies**

## **2025 Pricing Policy**

Effective during 2025:

* Enterprise Account Executives may approve discounts up to and including 15%.
* Discounts greater than 15% require VP Sales approval.
* Discounts must be calculated against the current list price.
* Contract-specific pricing exceptions must be reviewed.
Therefore:

On a date governed by the 2025 policy, Sarah Chen may independently approve a 15% discount, assuming the applicable contract and commercial requirements are satisfied.

---

## **2026 Pricing Policy**

Effective during 2026:

* Enterprise Account Executives may approve discounts up to and including 10%.
* Discounts greater than 10% and up to and including 20% require VP Sales approval.
* Discounts greater than 20% require CRO approval.
* Discounts are calculated against the current list price.
* Contract-specific pricing exceptions must be reviewed.
* Discounts greater than 10% require recorded approval evidence.
Therefore:

On 2026-09-23, Sarah Chen may not independently approve a 15% discount.

---

# **10. Approval Authority**

The canonical 2026 authority matrix is:

|  **Role**  |  **Discount authority**  | 
|---|---|
|  Enterprise Account Executive  |  ≤10%  |
|  VP Sales  |  >10% and ≤20%  |
|  Chief Revenue Officer  |  >20%  |
Authority is determined by the employee’s role and the policy effective at the time of the decision.

Contractual eligibility does not change employee authority.

---

# **11. Sales Discount Process**

The canonical process is:

```
Discount Request
      ↓
Identify Customer
      ↓
Identify Product
      ↓
Check Active Contract
      ↓
Check Pricing Exception
      ↓
Determine Applicable Policy
      ↓
Determine Requestor Authority
      ↓
Determine Required Approver
      ↓
Approve / Reject / Escalate
      ↓
Record Decision and Evidence
```

A request must not be approved solely because the requested commercial discount is permitted by a customer contract.

---

# **12. Orders**

## **SO-7001**

* Order ID: SO-7001
* Customer: CUST-1001
* Date: 2026-06-10
* Value: $480,000
* Status: Completed
## **SO-7002**

* Order ID: SO-7002
* Customer: CUST-1001
* Date: 2026-08-18
* Value: $720,000
* Status: Completed
These orders establish an existing commercial relationship with Acme.

---

# **13. Discount Request**

## **DR-9001**

* Discount Request ID: DR-9001
* Customer: CUST-1001
* Product: PROD-001
* Requested discount: 15%
* Requestor: EMP-101 / Sarah Chen
* Request date: 2026-09-23
* Expected pre-discount order value: $250,000
* Requested discount value: $37,500
* Expected net value: $212,500
---

# **14. Scenario 1 — Standard 15% Request**

### **Question**

Can Sarah Chen approve a 15% discount for Acme Manufacturing on an NS-500 Industrial Controller on 2026-09-23?

### **Ground-truth reasoning**

1. Acme is a valid Northstar customer.
2. CRM-2048, C-1001, and ACME-MFG-2025 refer to Acme Manufacturing.
3. The Acme master agreement is active.
4. Acme has an active 15% pricing exception for the NS-500.
5. The requested 15% discount is within the commercial eligibility granted to Acme.
6. The 2026 pricing policy applies.
7. Sarah Chen’s authority is limited to 10%.
8. 15% exceeds Sarah’s authority.
9. 15% falls within the VP Sales approval band.
10. Michael Torres is the VP Sales.
11. Michael is Sarah’s manager and has the required approval authority.

⠀
### **Expected outcome**

```
APPROVE_WITH_AUTHORIZATION
```

### **Required approver**

Michael Torres.

### **Key distinction**

```
Commercial eligibility: YES
Sarah's approval authority: NO
VP Sales authority: YES
```

---

# **15. Scenario 2 — 18% Request**

Change DR-9001’s requested discount from 15% to 18%.

### **Ground-truth reasoning**

* Acme’s contractual exception permits up to 15%.
* 18% exceeds the contractual exception.
* 18% is also above Sarah’s authority.
* Although 18% falls within the VP Sales approval band, the commercial eligibility itself is exceeded.
### **Expected outcome**

```
REJECT_OR_ESCALATE
```

The request requires additional commercial authorization or renegotiation of the applicable exception.

Michael’s approval authority alone does not create Acme’s commercial eligibility.

---

# **16. Scenario 3 — NS-Cloud Request**

Change the requested product from:

```
NS-500 Industrial Controller
```

to:

```
NS-Cloud Operations Suite
```

while retaining a 15% requested discount.

### **Ground-truth reasoning**

The Acme 15% exception applies specifically to the NS-500 Industrial Controller.

It does not automatically apply to NS-Cloud Operations Suite.

Therefore:

```
Acme customer eligibility: YES
NS-Cloud 15% exception: NO
Sarah authority: NO
```

### **Expected outcome**

```
REVIEW_REQUIRED
```

The system should not transfer a product-specific exception to another product.

---

# **17. Scenario 4 — Historical 15% Request**

Evaluate the equivalent 15% request on a date in September 2025.

### **Ground-truth reasoning**

The 2025 pricing policy was in effect.

Under that policy:

* Sarah’s approval authority extended to 15%.
* The Acme pricing exception was active.
* The NS-500 was covered by the exception.
### **Expected outcome**

```
APPROVE
```

assuming all other applicable commercial requirements are satisfied.

### **Important temporal distinction**

The answer changes because the organizational policy changed.

The underlying customer and contract did not necessarily change.

---

# **18. Scenario 5 — Missing Contract Evidence**

Remove the Acme master supply agreement and pricing exception from the available evidence.

Retain:

* CRM account
* ERP customer
* discount request
* 2026 pricing policy
* organization chart
### **Ground-truth reasoning**

The system knows:

* Acme exists.
* Sarah owns the account.
* Sarah cannot approve 15%.
* VP Sales approval is required.
But it does not have sufficient evidence to establish that Acme is commercially eligible for 15%.

### **Expected outcome**

```
REQUEST_EVIDENCE
```

The system should not infer the existence of the contractual exception merely because it has appeared elsewhere in historical knowledge.

---

# **19. Scenario 6 — Conflicting Exception Information**

Introduce an older Acme exception stating:

```
Maximum NS-500 discount = 10%
```

with an earlier effective period.

Introduce the current exception stating:

```
Maximum NS-500 discount = 15%
```

effective 2025-04-01 through 2028-03-31.

### **Ground-truth outcome**

The current 15% exception supersedes the older exception for dates within its validity period.

The older 10% exception remains historically valid for its own effective period.

### **Expected behavior**

The system should preserve both facts rather than overwrite the older fact.

It should select the fact applicable to the decision date.

---

# **20. Evidence Requirements**

Every consequential decision should be explainable through evidence.

For Scenario 1, the minimum evidence set is:

1. Acme identity / CRM account
2. ERP customer identity
3. Acme Master Supply Agreement
4. Acme pricing exception
5. 2026 pricing policy
6. Approval authority matrix
7. Organization chart
8. Discount request

⠀
The decision should be traceable back to these sources.

---

# **21. Canonical Decision Object**

The conceptual OWM decision representation is:

```
decision_id: DEC-9001

type: discount_approval

as_of: 2026-09-23

subject:
  customer: CUST-1001
  product: PROD-001

request:
  id: DR-9001
  requested_discount: 0.15
  requestor: EMP-101

commercial_eligibility:
  status: eligible
  maximum_discount: 0.15
  basis: EXC-ACME-NS500-15

authority:
  requestor:
    employee: EMP-101
    maximum_discount: 0.10
    authorized: false

  required:
    role: VP_SALES
    maximum_discount: 0.20

  approver:
    employee: EMP-200
    name: Michael Torres
    authorized: true

decision:
  outcome: APPROVE_WITH_AUTHORIZATION

reason:
  - customer exception permits requested discount
  - requestor lacks authority
  - VP Sales approval is required
  - Michael Torres holds VP Sales authority

evidence:
  - CRM-2048
  - C-1001
  - MSA-ACME-2025
  - EXC-ACME-NS500-15
  - pricing_policy_2026
  - approval_authority_matrix
  - organization_chart
  - DR-9001
```

---

# **22. What This Ground Truth Is Intended to Test**

The dataset should allow us to test whether the system can understand:

### **Identity**

Can multiple representations be recognized as the same organization?

### **Relationships**

Can the system understand who owns whom, who reports to whom, and which entity relates to which?

### **Semantics**

Can it distinguish a customer, account, contract, exception, policy, authority, and decision?

### **Temporal state**

Can it determine which policy or authority applies at a particular point in time?

### **Organizational authority**

Can it distinguish commercial eligibility from employee approval authority?

### **Exceptions**

Can it apply a narrowly scoped exception without generalizing it incorrectly?

### **Evidence**

Can every consequential conclusion be traced to supporting evidence?

### **Uncertainty**

Can the system recognize when evidence is insufficient rather than fabricate an answer?

### **Decisions**

Can organizational knowledge be transformed into a governed decision?

---

# **23. The Fundamental OWM Principle Demonstrated by Northstar**

The organization is not represented by any individual document or database.

It emerges from the relationships among:

```
People
  +
Roles
  +
Accounts
  +
Customers
  +
Products
  +
Contracts
  +
Policies
  +
Exceptions
  +
Authority
  +
Temporal State
  +
Evidence
  +
Decisions
```

The purpose of the Organizational World Model is to maintain this organizational understanding as an **evergreen, continuously enriched model**, rather than reconstructing it from scratch for every question.

The knowledge foundation provides the evidence.

The OWM provides the organizational meaning.

The decision layer applies that understanding to action.