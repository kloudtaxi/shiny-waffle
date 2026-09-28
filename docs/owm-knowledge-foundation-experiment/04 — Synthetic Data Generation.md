## 04 — Synthetic Data Generation

I would use **both, but for different jobs**. For this particular demo, I would make **Polyfactory the structural generator and Faker the primitive data generator**, rather than choosing one.

Polyfactory⁠![](file:///Attachment.png) is especially attractive because it generates from typed models and supports Pydantic, dataclasses, TypedDicts, SQLAlchemy, etc. It also supports deterministic seeding. 

### **The key distinction**

**Faker generates plausible values.**

```
Sarah Chen
Chicago
$247,382
2026-09-17
```

**Polyfactory generates plausible objects.**

```
Customer
  ├── Account
  ├── Contacts
  ├── Contracts
  └── Orders
```

And that’s much closer to what we’re trying to build.

But there’s an even more important point:

## **Don’t let either library generate the**

**meaning**

For our OWM dataset, I’d use three layers:

```
DOMAIN TRUTH
                      │
             ┌────────▼────────┐
             │ Scenario Model  │
             │                 │
             │ Acme            │
             │ Sarah           │
             │ Michael         │
             │ 15% exception   │
             │ authority       │
             │ temporal rules  │
             └────────┬────────┘
                      │
              deterministic
                  generation
                      │
             ┌────────▼────────┐
             │   Polyfactory   │
             │                 │
             │ entities        │
             │ accounts        │
             │ orders          │
             │ employees       │
             └────────┬────────┘
                      │
                 Faker values
                      │
             ┌────────▼────────┐
             │ Evidence Corpus │
             │                 │
             │ CSV             │
             │ Markdown        │
             │ emails          │
             │ contracts       │
             └─────────────────┘
```

### **In other words**

I would **hand-author the organizational truth**:

```
acme:
  canonical_id: CUST-1001
  aliases:
    - Acme Manufacturing
    - Acme Mfg. Holdings
    - Acme
  account_owner: EMP-101
  strategic: true
  discount_exception:
    product: PROD-001
    maximum: 0.15
    valid_from: 2025-04-01
    valid_to: 2028-03-31
```

Then let Polyfactory generate the boring stuff around it:

```
200 customers
40 employees
500 orders
80 products
1,000 CRM records
```

while Faker provides names, addresses, dates, phone numbers, descriptions, etc.

---

# **I’d actually build a small “Northstar Factory”**

Something like:

```
northstar/
├── model/
│   ├── entities.py
│   ├── relationships.py
│   ├── policies.py
│   └── scenarios.py
│
├── factories/
│   ├── customer.py
│   ├── employee.py
│   ├── product.py
│   ├── contract.py
│   ├── order.py
│   └── account.py
│
├── generators/
│   ├── crm.py
│   ├── erp.py
│   ├── documents.py
│   └── emails.py
│
└── export/
    ├── csv.py
    └── markdown.py
```

Polyfactory becomes the engine for the typed domain objects. It supports relationships and SQLAlchemy persistence as well, which gives us room to evolve this into a more realistic synthetic enterprise database later.

---

## **But here’s the part I think is particularly valuable for our experiment**

We should have a **“known truth” layer** that intentionally creates the difficult cases.

For example:

```
Scenario(
    name="acme_discount",
    customer="CUST-1001",
    product="PROD-001",
    requested_discount=0.15,
    requestor="EMP-101",
    as_of="2026-09-23",
    expected_decision="APPROVE_WITH_AUTHORIZATION",
)
```

Then the generator produces all the artifacts necessary to make that scenario true:

```
Scenario
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       CRM data     ERP data    Documents
          │            │            │
          └────────────┼────────────┘
                       ▼
                    Utopia
                       │
                       ▼
                      OWM
                       │
                       ▼
                 Expected decision
```

This means we can regenerate the entire dataset whenever we change the model.

That’s **much better than manually maintaining 15 CSVs and documents**.

---

# **One thing I would**

**not**

**do**

I wouldn’t generate a massive realistic enterprise dataset yet.

For the first iteration:

**~10 entities + ~20 relationships + ~10 documents + 5 scenarios** is enough.

The objective isn’t:

“Can we simulate an enterprise?”

It’s:

**“Can we discover the boundary between knowledge and organizational understanding?”**

Once that works, we can scale the generator to hundreds/thousands of records and see whether the OWM architecture continues to hold.

### **My recommendation**

**Use Polyfactory + Faker, but make neither the source of truth.**

I’d make:

**Scenario/Domain Truth → Polyfactory → Faker → Evidence Corpus → Utopia → OWM evaluation**

And because this is a learning experiment, I’d make the generator **seeded and reproducible**. Polyfactory explicitly supports seeded randomness, including its Faker integration, so we can regenerate exactly the same corpus while changing the OWM implementation. 

That gives us something much more valuable than a one-off demo dataset: **a synthetic enterprise laboratory for OWM.** 