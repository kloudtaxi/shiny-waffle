## A001 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller was **10% off list price**.

**Why 10%:**
- **Pricing exception EXC-ACME-NS500-10** (Deal Desk, under agreement ACME-SA-2023) says: "Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31." 2024-10-01 falls inside that window.

**Why not 15%:**
- The 15% comes from the later **Master Supply Agreement ACME-MFG-2025** (section 3.2) and its Schedule B, **EXC-ACME-NS500-15**. Both run from 2025-04-01 to 2028-03-31.
- EXC-ACME-NS500-15 replaces the 10% exception only "for requests dated on or after 2025-04-01." So it doesn't apply to 2024-10-01.

Sarah Chen's account strategy note and her DR-9001 email both assume Acme's terms allow 15%. That's only true from 2025-04-01 onward. Also, these exceptions only set what Acme is eligible for. They don't give any Northstar employee the authority to approve a discount.

---

## A002 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01 was **10% off list price**.

**Where this comes from:**
- **The applicable term:** The "Acme NS-500 Volume Pricing Exception" document says, under agreement ACME-SA-2023: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31."* 2024-10-01 falls inside that window. The document also gives the agreement's status as Active.
- **Why it isn't 15%:** The newer exception, EXC-ACME-NS500-15, allows up to 15%. It is Schedule B to agreement ACME-MFG-2025, was approved by David Morgan on 2025-03-20, and runs from 2025-04-01 to 2028-03-31. It replaces EXC-ACME-NS500-10 only *"for requests dated on or after 2025-04-01,"* so it didn't apply yet on 2024-10-01.
- **Customer:** ACME Manufacturing is listed as CRM-2048 and as ERP customer C-1001, where it appears under the name "Acme Mfg. Holdings."

**Things to keep in mind:**
- The knowledge base doesn't explicitly link the exception ID "EXC-ACME-NS500-10" to the Volume Pricing Exception document. The 10% figure and the dates make it very likely they are the same exception, but that isn't confirmed.
- This 10% is a limit on what the customer could receive. It doesn't give any employee the authority to approve that discount. Approval still depends on the requestor's limit under the discount policy in force at the time.

---

## A003 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers point to one customer, **Acme Manufacturing**. **Acme Industrial Supply Co. is a different company.**

**The three identifiers**

| Identifier | System | What it is | Name used there |
|---|---|---|---|
| CRM-2048 | CRM | Account | Acme Manufacturing (Strategic tier, Midwest Enterprise, owner Sarah Chen) |
| C-1001 | ERP | Customer (bill-to) | Acme Mfg. Holdings (Net 45) |
| ACME-MFG-2025 | Contract | Agreement with Acme Manufacturing | — |

- **CRM-2048 and C-1001 are the same company.** The CRM and ERP use different names, but both records give the same address (2200 N Industrial Pkwy, Milwaukee, WI) and the same DUNS number (04-812-7730). The account documentation also links them directly: "CRM account: CRM-2048" and "ERP bill-to: Acme Mfg. Holdings (C-1001)".
- **ACME-MFG-2025 is the customer's agreement, not a customer ID.** Its schedules name Acme Manufacturing as the customer:
  - Schedule B is the *Acme NS-500 Strategic Account Exception*, with Acme Manufacturing as the customer.
  - Schedule C (Support and Service Levels) says "Northstar Industrial Systems provides support to Acme Mfg. Holdings". It took effect 2025-04-01.

**Acme Industrial Supply Co. is a separate customer.**
- **Different identifiers:** CRM-2091, ERP C-1044 and DUNS 09-552-1187.
- **Different details:** a different address (17 Tallmadge Ave, Akron, OH), a different industry (Industrial Distribution), Standard tier, and a different account owner (Zachary Brown).
- **Not covered by the agreement:** Schedule C to ACME-MFG-2025 says plainly: "Acme Industrial Supply Co. is a different company and is not covered." The same schedule also excludes the parent company, Acme Group Holdings, Inc., and any other affiliates.

This means ACME-MFG-2025's terms, including the NS-500 pricing exception and Platinum support, apply only to Acme Manufacturing (CRM-2048 / C-1001). They don't apply to Acme Industrial Supply Co. or to other Acme-named companies.

---

## A004 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off list price on the NS-500 Industrial Controller because of a customer contract and the pricing exception attached to it. Both run from 1 April 2025 to 31 March 2028, so both are in force today (17 Oct 2026). This makes Acme commercially eligible for the discount. It does not approve any particular request.

**1. Master Supply Agreement ACME-MFG-2025** (`acme_master_supply_agreement.md`)
- The contract is between Northstar Industrial Systems and Acme Mfg. Holdings, which trades as Acme Manufacturing. These are the same customer under two names (CRM account CRM-2048, DUNS 04-812-7730, Milwaukee, WI).
- §1 Term: "effective April 1, 2025 and expires March 31, 2028." Either party can end it early only for material breach, on 60 days' written notice (§9).
- §2: NS-500 is one of the products supplied under the agreement.
- §3.2: "Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller, as set out in the pricing exception attached as Schedule B."
- Signed by David Morgan (Chief Revenue Officer) on 2025-03-20 and by Edward Floyd (Acme, VP Procurement) on 2025-03-22.

**2. Pricing exception EXC-ACME-NS500-15** (Schedule B, `acme_pricing_exception.md`)
- Customer: Acme Manufacturing. Product: "NS-500 Industrial Controller (NS-500) only." Maximum: "15% of list price." Effective 2025-04-01, expires 2028-03-31.
- Prepared by Sarah Chen, the account owner. Approved by David Morgan, CRO, on 2025-03-20.
- It "supersedes EXC-ACME-NS500-10 for requests dated on or after 2025-04-01."

**Limits on that eligibility**
- **NS-500 only.** The exception "does not apply to any other Northstar product." Other products in the agreement, such as NS-CLOUD and NS-EDGE, don't get the 15%.
- **Dates.** It covers requests dated 1 April 2025 to 31 March 2028. Before that, the older exception EXC-ACME-NS500-10 (under agreement ACME-SA-2023) allowed only up to 10%, for orders from 1 April 2023 to 31 March 2025. That document still says "Status: Active", but it expired and has been replaced, so don't rely on it.
- **It doesn't give anyone approval authority.** The exception "establishes commercial eligibility only. It does not grant approval authority to any Northstar employee." MSA §3.3 says the same: each discount "remains subject to approval under Northstar's internal policies." Any actual 15% request still has to be approved by whoever the discount policy names for a 15% discount. I haven't looked up the policy bands because you didn't ask about a specific request.

---

## A005 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off the NS-500 because of a signed pricing exception attached to its 2025 contract. That exception makes Acme eligible for the discount. It doesn't approve any particular request, and it doesn't let any employee approve one.

**The source: exception EXC-ACME-NS500-15**
- **Document:** "Acme NS-500 Strategic Account Exception", stated to be "Schedule B to agreement ACME-MFG-2025". The Deal Desk owns it.
- **Customer:** "Acme Manufacturing". This is the same company as CRM account CRM-2048 and ERP customer C-1001 ("Acme Mfg. Holdings"). The contract says "Acme Mfg. Holdings, doing business as Acme Manufacturing", and the DUNS number 04-812-7730 matches in both systems.
- **Maximum:** "Maximum eligible discount | 15% of list price".
- **Product:** "NS-500 Industrial Controller (NS-500) only". It also says: "It does not apply to any other Northstar product."
- **Dates:** effective 2025-04-01, expires 2028-03-31. Today's date (2026-10-18) falls inside that window.
- **Approval:** prepared by Sarah Chen, who owns the Acme account in CRM. Approved by David Morgan on 2025-03-20.

**Why it's 15% and not 10%**
- The earlier exception, EXC-ACME-NS500-10 under agreement ACME-SA-2023, allowed "up to 10% off list price on the NS-500" for orders placed from 2023-04-01 to 2025-03-31.
- The 15% exception says "Supersedes EXC-ACME-NS500-10" for requests dated on or after 2025-04-01.
- The old document still shows "Status: Active", but its order window has ended and it has been replaced. For current requests the limit is 15%, not 10%.

A CRM account note also says Acme "negotiated preferential NS-500 pricing in the 2025 agreement" and that 15% was "approved for them last September". That backs up the exception, but the exception itself is the actual source.

**Limits on what this means**
1. **15% is a ceiling.** Anything above 15% is outside Acme's eligibility and would need new or amended terms. A more senior approver can't fix that.
2. **It doesn't approve anything by itself.** The exception says: "This exception establishes commercial eligibility only. It does not grant approval authority to any Northstar employee." Any 15% request still needs someone with enough authority under the discount policy in force on the request date. Being eligible under the contract doesn't change who can approve.
3. **It covers the NS-500 only.** It doesn't cover other products, such as the NS-Cloud product Acme is evaluating.
4. **One gap: the main contract's dates.** The knowledge base has no start or end date for agreement ACME-MFG-2025 itself. The exception's own dates cover today, but if you're deciding a specific request, you should confirm that agreement is still active on the request date.

If you have a specific 15% request to decide, send me its ID and I'll check the requestor's authority and who needs to approve it.

---

## A006 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 was **10% off list price**.

**Where this comes from:**
- **Exception EXC-ACME-NS500-10** (the "Acme NS-500 Volume Pricing Exception", under agreement ACME-SA-2023, owned by Deal Desk) says: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) … for orders placed from 2023-04-01 to 2025-03-31."* That period includes 2024-10-01.
- **The later 15% exception doesn't apply yet.** EXC-ACME-NS500-15, the "Strategic Account Exception" (Schedule B to agreement ACME-MFG-2025), raises the maximum to 15% of list price. But it only runs from 2025-04-01 to 2028-03-31, and it replaces the 10% exception only for "requests dated on or after 2025-04-01."

**Two things to keep in mind:**
- The knowledge base still lists the 10% exception's status as "Active." Its own wording limits it to orders placed between 2023-04-01 and 2025-03-31, so the status doesn't change the answer for 2024-10-01.
- An account note mentions a 15% NS-500 discount "approved for them last September," but it doesn't give a year. That 15% could only have been contractual from 2025-04-01 onward, so it doesn't change the 10% maximum on 2024-10-01. Both exceptions say they set what the customer is eligible for, not who can approve it. Any actual discount still needs approval by someone with authority under the discount policy.

Acme Manufacturing is CRM account CRM-2048 and ERP customer C-1001 (billed as "Acme Mfg. Holdings").

---

## A007 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 is **15% off list price**.

- **Where it comes from:** Pricing exception EXC-ACME-NS500-15 ("Acme NS-500 Strategic Account Exception") sets the 15%. It is attached as Schedule B to agreement ACME-MFG-2025, Acme's Master Supply Agreement, and Section 3.2 of that agreement repeats the 15% for the NS-500. Both the exception and the agreement run from 2025-04-01 to 2028-03-31, so they cover 2026-09-23. I didn't find anything showing the agreement was terminated early.
- **Which customer:** "Acme Manufacturing" is the trading name of Acme Mfg. Holdings, which is CRM account CRM-2048 and ERP customer C-1001. It is a different company from Acme Industrial Supply Co.
- **Product only:** The exception covers only the NS-500 Industrial Controller, not any other Northstar product.
- **The older 10% limit no longer applies:** Exception EXC-ACME-NS500-10 under agreement ACME-SA-2023 allowed up to 10% for orders from 2023-04-01 to 2025-03-31. EXC-ACME-NS500-15 replaces it for requests dated on or after 2025-04-01. The older document's "Status: Active" label is out of date.
- **Eligibility isn't approval:** The exception states that it "establishes commercial eligibility only" and does not give any employee approval authority. Section 3.3 of the agreement says the same. Any discount still needs approval under Northstar's internal policy.

One related item: request DR-9001 is a pending request dated 2026-09-23 for 15% on the NS-500 for CRM-2048, submitted by Sarah Chen. 15% is within the contractual maximum, but whether she can approve it herself depends on the discount policy in force on that date. I haven't checked that policy. If you want a decision on DR-9001, I can run it through the full approval procedure.

---

## A008 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller is **15% off list price**.

**Where this comes from:**
- **Contract in force:** The Master Supply Agreement **ACME-MFG-2025** is between Northstar Industrial Systems and Acme Mfg. Holdings, which trades as Acme Manufacturing (CRM-2048 / ERP C-1001). It runs from 2025-04-01 to 2028-03-31, so it covers 2026-09-23. It says: *"Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller."*
- **Pricing exception:** Schedule B to that agreement is exception **EXC-ACME-NS500-15** ("Acme NS-500 Strategic Account Exception"). It also runs from 2025-04-01 to 2028-03-31 and sets a "Maximum eligible discount" of 15% of list price. It applies to the NS-500 only and to no other Northstar product. David Morgan approved it on 2025-03-20.
- **Older 10% exception no longer applies:** EXC-ACME-NS500-10, the "Volume Pricing Exception" under ACME-SA-2023, allowed up to 10%. It only covered orders placed from 2023-04-01 to 2025-03-31, and EXC-ACME-NS500-15 replaced it for requests dated 2025-04-01 or later. That document is still marked "Status: Active" in the knowledge base, so the label is out of date and could mislead someone.

The 15% cap only sets what Acme can be offered. It doesn't give anyone the authority to approve the discount. Both the agreement and the exception say each discount still needs approval under Northstar's internal discount policy.

---

## A009 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers refer to one customer: **Acme Mfg. Holdings, which does business as Acme Manufacturing**, at 2200 N Industrial Pkwy, Milwaukee, WI 53209 (DUNS 04-812-7730). **Acme Industrial Supply Co. is a different company.**

**The three identifiers**

| Identifier | System | What it is | Evidence |
|---|---|---|---|
| CRM-2048 | CRM | The account "Acme Manufacturing" (Strategic tier, Midwest Enterprise, owner Sarah Chen) | crm_accounts.csv; Account Strategy 2026 ("CRM account: CRM-2048") |
| C-1001 | ERP | The customer "Acme Mfg. Holdings", billed in Milwaukee, Net 45 | customers.csv; Account Strategy 2026 ("ERP bill-to: Acme Mfg. Holdings (C-1001)") |
| ACME-MFG-2025 | Contract | The Master Supply Agreement with "Acme Mfg. Holdings, doing business as Acme Manufacturing", effective 2025-04-01 to 2028-03-31 | Master Supply Agreement. Schedule B (pricing exception EXC-ACME-NS500-15) and Schedule C (Support) belong to it. |

The CRM and ERP use different names, but both records show the same Milwaukee address and the same DUNS number (04-812-7730). That confirms they are the same company.

**Acme Industrial Supply Co. is a separate customer**
- Its own identifiers are CRM-2091 (CRM sometimes shortens the name to "Acme Industrial") and ERP C-1044.
- It is in Akron, OH (17 Tallmadge Ave), its industry is Industrial Distribution, and its DUNS number is 09-552-1187. Its CRM account is Standard tier, Midwest Mid-Market, owned by Zachary Brown.
- The contract says so directly. Schedule C to ACME-MFG-2025 states: *"Acme Industrial Supply Co. is a different company and is not covered."* It also excludes the parent company, Acme Group Holdings, Inc., and all other affiliates.
- So the terms under ACME-MFG-2025 do not apply to Acme Industrial Supply Co. That includes the NS-500 pricing exception and the Platinum support plan. One of its service tickets (SR-39802) says "We're Acme. We have the Acme Platinum support plan." That claim isn't supported: the ticket is filed under CRM-2091, and the Platinum plan covers only Acme Mfg. Holdings.

**Problems in the knowledge base's identifier records:**
- Looking up CRM-2048 by itself returns a service ticket (SR-39385), and looking up C-1001 returns an invoice (INV-62011). Those records only mention the identifiers. The customer is the "ACME Manufacturing" entity, which holds both identifiers.
- Acme Industrial Supply Co. has two duplicate entities, one built from ERP data and one from CRM data. They share the same DUNS number, so they are one company. One of the two is described as coming from the Acme Manufacturing Schedule C, but that schedule only mentions the company to exclude it, so the description is misleading.

---

## A010 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers point to the same customer, **Acme Manufacturing** (canonical name "ACME Manufacturing"). **Acme Industrial Supply Co. is a different customer.**

**How each identifier maps**

| Identifier | System | What it is |
|---|---|---|
| **CRM-2048** | CRM | The account record "Acme Manufacturing": Strategic tier, Midwest Enterprise, 2200 N Industrial Pkwy, Milwaukee, WI. The account owner is Sarah Chen. |
| **C-1001** | ERP | The bill-to customer "Acme Mfg. Holdings", at the same Milwaukee address. The account brief says it directly: "CRM account: CRM-2048 … ERP bill-to: Acme Mfg. Holdings (C-1001)". |
| **ACME-MFG-2025** | — | Not an account number. It's the customer's agreement. Two documents sit under it, and both name Acme Manufacturing as the customer: the Acme NS-500 Strategic Account Exception ("Schedule B to agreement ACME-MFG-2025") and Schedule C, Support and Service Levels ("Schedule C … to ACME-MFG-2025"). |

The CRM and ERP names differ, but the two records also share DUNS number **04-812-7730**, which confirms they are one company. The agreement is tied to the customer only through those two schedules. The knowledge base has no direct record saying "ACME-MFG-2025 is with Acme Manufacturing."

**Acme Industrial Supply Co.**
- It has its own records: CRM **CRM-2091** (Standard tier, Midwest Mid-Market), ERP **C-1044**, and DUNS **09-552-1187**. Its address is 17 Tallmadge Ave, Akron, OH, and its account owner is Zachary Brown.
- Schedule C to ACME-MFG-2025 says so directly: *"Acme Industrial Supply Co. is a different company and is not covered."*
- So none of Acme Manufacturing's terms apply to it, including the agreement, the NS-500 exception and the support schedule.

**Related names to keep separate**
- **Acme Group Holdings, Inc.** is recorded as Acme Manufacturing's parent. Schedule C says the parent is not covered.
- Schedule C also excludes "Acme Mfg. Holdings affiliates".

The knowledge base also has a few other organizations called just "Acme", "ACME Mfg" or "Acme Group". They come from loosely worded sources and shouldn't be matched to either customer without more evidence.

---

## A011 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

I found no contractual NS-500 discount for Acme Manufacturing on 2022-10-01, so there is no contractual maximum on that date. Both Acme NS-500 discount terms in the knowledge base start later:

| Term | Max NS-500 discount | Period |
|---|---|---|
| EXC-ACME-NS500-10 (agreement ACME-SA-2023) | 10% off list price | Orders placed 2023-04-01 to 2025-03-31 |
| EXC-ACME-NS500-15 (Master Supply Agreement §3.2, Schedule B) | 15% of list price | 2025-04-01 to 2028-03-31; replaces the 10% term from 2025-04-01 |

- The 10% term covers only orders from 2023-04-01 to 2025-03-31. 2022-10-01 is six months before it starts.
- The 15% term and the Master Supply Agreement run from 2025-04-01 to 2028-03-31.
- I found nothing in the knowledge base giving Acme special NS-500 pricing before 2023-04-01. (Acme Manufacturing is the trading name of Acme Mfg. Holdings, CRM-2048 / ERP C-1001.)

On 2022-10-01, Acme would have been on standard pricing under the discount policy in force at the time. Special terms only cover the dates they name, so neither the 10% nor the 15% term can be applied backwards. If someone says an earlier Acme agreement existed before 2023, ask them for the document. The knowledge base doesn't hold one.

---

## A012 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 was **10% off list price**.

**Where the 10% comes from:** The Acme NS-500 Volume Pricing Exception (**EXC-ACME-NS500-10**) sets this limit. It is attached to agreement ACME-SA-2023, is owned by the Deal Desk, and its status is "Active." It says: *"Acme Manufacturing may receive up to 10% off list price on the NS-500 Industrial Controller (NS-500)… for orders placed from 2023-04-01 to 2025-03-31."* 2024-10-01 falls inside that period.

**Why it isn't 15%:** The Acme NS-500 Strategic Account Exception (**EXC-ACME-NS500-15**, Schedule B to agreement ACME-MFG-2025) raises the maximum to 15% of list price. But it only takes effect on 2025-04-01, which is after the date you asked about. It replaces the 10% exception only for requests dated on or after 2025-04-01, and it runs until 2028-03-31.

**Two things to keep in mind:**
- An account note says Acme was given 15% on the NS-500 "last September." If that refers to September 2024, it went over the 10% limit in force at the time, because the 15% exception didn't exist yet.
- Both exceptions cover the NS-500 only. They are about what the customer may receive, and they don't give any employee approval authority. So a discount within 10% on that date still needed approval under the discount policy in force.

The customer is the same in both systems: Acme Manufacturing is CRM account CRM-2048 and ERP customer C-1001, which the ERP lists as "Acme Mfg. Holdings."

---

## A013 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers refer to the same customer: **Acme Mfg. Holdings, doing business as Acme Manufacturing**, at 2200 N Industrial Pkwy, Milwaukee, WI 53209. **Acme Industrial Supply Co. is a different customer.**

**How the three identifiers connect**

| Identifier | Where it's used | Name on the record | Address | DUNS |
|---|---|---|---|---|
| **CRM-2048** | CRM account (Strategic, Midwest Enterprise; owner Sarah Chen) | Acme Manufacturing | 2200 N Industrial Pkwy, Milwaukee, WI | 04-812-7730 |
| **C-1001** | ERP customer (Net 45) | Acme Mfg. Holdings | 2200 N Industrial Pkwy, Milwaukee, WI 53209 | 04-812-7730 |
| **ACME-MFG-2025** | Master Supply Agreement (1 Apr 2025 – 31 Mar 2028) | Acme Mfg. Holdings, doing business as Acme Manufacturing | 2200 N Industrial Pkwy, Milwaukee, WI 53209 | — |

- **The CRM and ERP names match:** the 2026 account strategy says "CRM account: CRM-2048 … ERP bill-to: Acme Mfg. Holdings (C-1001)". Both records also have the same address and DUNS number.
- **The agreement is with the same company:** ACME-MFG-2025 names "Acme Mfg. Holdings, doing business as Acme Manufacturing" at that address. Its Schedule C names Acme Mfg. Holdings with the same DUNS (04-812-7730). Its Schedule B is pricing exception EXC-ACME-NS500-15, which gives up to 15% off the NS-500 controller.
- Service tickets under CRM-2048 also use the names "Acme Manufacturing" and "Acme Mfg. Holdings" for the Milwaukee plants.

**Acme Industrial Supply Co. is a different company**

| | Acme Manufacturing / Acme Mfg. Holdings | Acme Industrial Supply Co. |
|---|---|---|
| CRM account | CRM-2048 (Strategic, Midwest Enterprise) | CRM-2091 (Standard, Midwest Mid-Market) |
| ERP customer | C-1001 | C-1044 |
| Industry | Industrial Manufacturing | Industrial Distribution |
| Address | 2200 N Industrial Pkwy, Milwaukee, WI | 17 Tallmadge Ave, Akron, OH 44310 |
| DUNS | 04-812-7730 | 09-552-1187 |
| Account owner | Sarah Chen | Zachary Brown |

Acme Industrial Supply Co. has its own IDs, address, DUNS number and industry, and none of the Acme agreements or pricing exceptions name it. The terms in ACME-MFG-2025 and EXC-ACME-NS500-15, including the 15% NS-500 pricing, don't apply to it.

**Two things to watch:**
- The knowledge base splits this one customer into several entries ("Acme", "Acme Manufacturing" and "Acme Mfg. Holdings"). Look up by ID or DUNS number rather than by name.
- "Acme Industrial" is also listed as an alternative name for the generic "Acme" entry. Don't let it get mixed up with Acme Industrial Supply Co.

---

## A014 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

On 2022-10-01, Acme Manufacturing had no contractual NS-500 discount that I can find, so there's no contractual maximum for that date. Both documented terms start later:

| Term | Max NS-500 discount | Valid for |
|---|---|---|
| EXC-ACME-NS500-10 (under agreement ACME-SA-2023) | 10% off list | Orders placed 2023-04-01 to 2025-03-31 |
| EXC-ACME-NS500-15 (Schedule B to Master Supply Agreement ACME-MFG-2025) | 15% off list | 2025-04-01 to 2028-03-31; replaced the 10% exception from 2025-04-01 |

- **The 10% term started six months too late.** It was written on 2023-03-12 and says it covers orders "from 2023-04-01 to 2025-03-31". That document does say "Status: Active", but it gives no earlier start date.
- **No earlier agreement shows up.** I searched for 2021–2022 Acme agreements or pricing terms and found none.

So an NS-500 discount for Acme dated 2022-10-01 would fall under standard pricing, with no special terms. If someone says an earlier contract or exception covered that date, ask for the document. Nothing in the records supports it.

---

## A015 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

On 2022-10-01, the knowledge base shows **no contractual NS-500 discount maximum for Acme Manufacturing**. Every NS-500 discount term it holds for Acme starts later than that date.

**Acme's NS-500 discount terms by date:**

| Term | Maximum | Applies | Source |
|---|---|---|---|
| EXC-ACME-NS500-10 (Volume Pricing Exception, linked to agreement ACME-SA-2023) | 10% off list price | Orders placed 2023-04-01 to 2025-03-31 | "Acme Manufacturing may receive up to 10% off list price on the NS-500 Industrial Controller (NS-500)… for orders placed from 2023-04-01 to 2025-03-31" |
| EXC-ACME-NS500-15 (Schedule B to Master Supply Agreement ACME-MFG-2025) | 15% of list price | 2025-04-01 to 2028-03-31 (replaces the 10% exception from 2025-04-01) | "Maximum eligible discount: 15% of list price" |

- 2022-10-01 falls before both, so neither applies, and the knowledge base has no earlier Acme contract or exception.
- The 10% exception is the earliest (created 2023-03-12). The record for its agreement, ACME-SA-2023, has no start or end dates, so nothing shows a term covering late 2022.
- The 10% and 15% limits don't carry backwards: an exception only covers the product and dates it names.

**What this means:** For an NS-500 discount dated 2022-10-01, Acme has no special terms on record, so only standard pricing applies. If a request dated then relies on a contract term, the procedure says to ask for that document before deciding.

(Acme Manufacturing is the same customer as CRM account CRM-2048 and ERP customer C-1001, billed as "Acme Mfg. Holdings".)

---

## A016 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller is **15% of list price**. Two documents give that figure and they agree:

1. **The contract was in force.** The Master Supply Agreement, reference ACME-MFG-2025, is between Northstar Industrial Systems and Acme Mfg. Holdings, which trades as Acme Manufacturing (CRM-2048 / ERP C-1001). It runs from 2025-04-01 to 2028-03-31 and says "Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller." It was signed by David Morgan (CRO) and Edward Floyd (Acme VP Procurement).
2. **A pricing exception sets the same cap for this product.** The Acme NS-500 Strategic Account Exception, EXC-ACME-NS500-15, is Schedule B to ACME-MFG-2025. It runs from 2025-04-01 to 2028-03-31, covers the NS-500 only, and sets the "Maximum eligible discount" at 15% of list price. David Morgan approved it on 2025-03-20.
3. **The older exception no longer applies.** EXC-ACME-NS500-10 was replaced for requests dated on or after 2025-04-01, so it doesn't cover this date.

**Limits on the 15%:**
- It applies only to the NS-500, not to other Northstar products.
- It sets what Acme can receive commercially. It doesn't give any Northstar employee the authority to approve a discount. The agreement says each discount still needs approval under Northstar's internal policies.

The discount request open on that date, DR-9001, asks for exactly 15% on the NS-500 (list price $250,000, net $212,500). It's still Pending Approval, so it's within Acme's limit but still needs approval from someone with authority under the discount policy.

---

## A017 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

I couldn't find any contractual NS-500 discount for Acme Manufacturing on 2022-10-01. Nothing in the knowledge base sets a maximum for that date. Acme Manufacturing goes by "Acme Mfg. Holdings" in the ERP (C-1001) and is CRM-2048 in the CRM.

Only two documents set a maximum NS-500 discount for Acme, and both start after that date:

| Exception | Agreement | Maximum | Valid |
|---|---|---|---|
| EXC-ACME-NS500-10 (Volume Pricing Exception) | ACME-SA-2023 | 10% off list | Orders placed **2023-04-01 to 2025-03-31** |
| EXC-ACME-NS500-15 (Strategic Account Exception, Schedule B) | ACME-MFG-2025 (Master Supply Agreement, effective 2025-04-01 to 2028-03-31) | 15% off list | **2025-04-01 to 2028-03-31**; replaces the 10% exception for requests from 2025-04-01 |

- **On 2022-10-01:** no NS-500 discount entitlement is on record. Neither exception had started, and the earliest Acme agreement on file (ACME-SA-2023) doesn't cover that date either. Standard pricing would apply unless an older contract or exception exists outside the knowledge base. A request from that date relying on contract terms would need that document before anyone could decide it.
- **Watch the "Status: Active" label on the 10% exception.** It's out of date: the exception ended on 2025-03-31 and the 15% exception replaced it.
- **The maximum only limits what the customer can get.** Both the Master Supply Agreement (§3.3) and the exception itself say they don't change Northstar's internal approval authority. Any discount still needs approval under the policy in force on the request date.

---

## A018 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 was **10% off list price**.

- **The exception that applied:** EXC-ACME-NS500-10, the "Acme NS-500 Volume Pricing Exception" under agreement ACME-SA-2023. It says Acme Manufacturing "may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31." 2024-10-01 falls inside that period. The document's status reads "Active."
- **Why it isn't 15%:** The 15% figure comes from EXC-ACME-NS500-15, which is Schedule B to agreement ACME-MFG-2025 and section 3.2 of the Master Supply Agreement. That exception runs from 2025-04-01 to 2028-03-31 and replaces the 10% exception only "for requests dated on or after 2025-04-01." It didn't apply yet on 2024-10-01.
- **Account names:** Acme Manufacturing is CRM account CRM-2048. In the ERP it is customer C-1001, under the name "Acme Mfg. Holdings."

The 10% only sets what the customer is commercially eligible for. It doesn't give any employee the authority to approve a discount, which still has to go through the internal approval policy in force at the time. The 2026 account strategy note's guess that the 15% applied "last September" is about 2025, not 2024.

---

## A019 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off the NS-500 because two documents say so: its Master Supply Agreement (ACME-MFG-2025), and a pricing exception attached to that agreement as Schedule B. Both were in force on 2026-09-23, the date of request DR-9001. But being eligible for 15% does not mean the discount is approved.

**Same customer in both systems.** The CRM account is CRM-2048 "Acme Manufacturing" (Strategic, owner Sarah Chen). The ERP customer is C-1001 "Acme Mfg. Holdings". They share DUNS 04-812-7730 and the address 2200 N Industrial Pkwy, Milwaukee. The agreement names the customer as "Acme Mfg. Holdings, doing business as Acme Manufacturing".

**Evidence**

1. **Master Supply Agreement, ACME-MFG-2025**
   - It is between Northstar Industrial Systems and Acme Mfg. Holdings. David Morgan (Chief Revenue Officer) signed for Northstar and Edward Floyd (VP Procurement) signed for Acme.
   - It runs from 2025-04-01 to 2028-03-31, and either side can end it early for material breach on 60 days' notice.
   - Products it covers: NS-500 Industrial Controller, NS-Cloud Operations Suite and NS-Edge Monitoring Package.
   - The discount clause: *"Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller."*
   - It adds: *"Each discount remains subject to approval under Northstar's internal policies."*

2. **Acme NS-500 Strategic Account Exception, EXC-ACME-NS500-15** (Schedule B to ACME-MFG-2025)
   - Customer: Acme Manufacturing. Product: *"NS-500 Industrial Controller (NS-500) only"*. It *"does not apply to any other Northstar product."*
   - Maximum eligible discount: *"15% of list price."*
   - It runs from 2025-04-01 to 2028-03-31. Sarah Chen prepared it and David Morgan approved it on 2025-03-20. Deal Desk owns it.
   - It *"Supersedes EXC-ACME-NS500-10 for requests dated on or after 2025-04-01."*

3. **The older 10% terms no longer apply.** The earlier agreement, ACME-SA-2023, allowed up to 10% on the NS-500 for orders from 2023-04-01 to 2025-03-31. That period ended, and the 15% exception replaced the old 10% exception. The 2023 record still shows "Status: Active", but for a request dated 2026 the 15% terms are the ones that count.

**The request this applies to.** DR-9001 in the CRM: CRM-2048, NS-500, 15.0% off a list price of $250,000 ($37,500 discount, $212,500 net). Sarah Chen submitted it on 2026-09-23, citing "Contract pricing per Acme Master Supply Agreement." It is still Pending Approval. 15% equals the ceiling, so it does not go over it.

**What this does not settle.** The exception says it *"establishes commercial eligibility only"* and *"does not grant approval authority to any Northstar employee."* The agreement also leaves each discount subject to Northstar's internal approval. So eligibility is settled, but approving DR-9001 still depends on the requestor's authority under the discount policy in force on 2026-09-23. I didn't check that policy or its approval bands, because you asked about eligibility. If you want an approve-or-not decision on DR-9001, I can do that next.

---

## A020 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off the NS-500 because of a pricing exception, **EXC-ACME-NS500-15**. That eligibility applies to orders from 2025-04-01 to 2028-03-31. It does not authorise any particular person to approve a 15% discount.

**What the exception says** (all quotes from one exception document):
- **Customer:** "| Customer | Acme Manufacturing |"
- **Product:** "| Product | NS-500 Industrial Controller (NS-500) only |". It also says "It does not apply to any other Northstar product."
- **Maximum discount:** "| Maximum eligible discount | 15% of list price |"
- **Dates:** "| Effective | 2025-04-01 |" and "| Expires | 2028-03-31 |"
- **It replaces the old 10% exception:** "Supersedes EXC-ACME-NS500-10 for requests dated on or after 2025-04-01."
- **Who signed it off:** "Exception approved by: David Morgan, Chief Revenue Officer, 2025-03-20." It was prepared by Sarah Chen, the CRM account owner for Acme.

**The earlier terms.** Under agreement ACME-SA-2023, exception EXC-ACME-NS500-10 allowed "up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31." So for a request dated before 2025-04-01, the maximum is 10%, not 15%.

**The current contract.** The Master Supply Agreement is between Northstar Industrial Systems and "Acme Mfg. Holdings, doing business as Acme Manufacturing". It "is effective April 1, 2025 and expires March 31, 2028." Those are the same dates as the 15% exception. Acme Manufacturing's CRM account is CRM-2048, status Active.

**Limits on what this gives you:**
- **Only the NS-500.** The 15% doesn't apply to any other Northstar product.
- **It doesn't give anyone authority to approve.** The document says: "This exception establishes commercial eligibility only. It does not grant approval authority to any Northstar employee." A request for 15% must still be approved by whoever the discount policy in force on the request date says can approve 15%. The fact that the exception allows it is not enough on its own.
- **15% is a ceiling.** A request above 15% would need new or amended terms, not just a more senior approver.

**A data error to fix:** the knowledge base has a fact saying Northstar does business as Acme Manufacturing. That was read wrongly from the contract. The contract says it is Acme Mfg. Holdings that does business as Acme Manufacturing.

---

## A021 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing could receive a contractual discount of up to **15% off list price on the NS-500**. Two current documents give that figure, and both cover that date:

- **Master Supply Agreement ACME-MFG-2025** (Northstar and Acme Mfg. Holdings, doing business as Acme Manufacturing) says: "Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller." It runs from 2025-04-01 to 2028-03-31. It can be ended early for material breach on 60 days' notice, but nothing in the records shows that happened.
- **Exception EXC-ACME-NS500-15** (the "Acme NS-500 Strategic Account Exception", Schedule B to ACME-MFG-2025) sets a maximum of 15% of list price. It covers the NS-500 only and runs from 2025-04-01 to 2028-03-31. David Morgan approved it on 2025-03-20.

**Earlier terms that no longer apply:** the 10% discount under ACME-SA-2023 (the "Volume Pricing Exception") covered orders placed from 2023-04-01 to 2025-03-31. EXC-ACME-NS500-15 also replaces EXC-ACME-NS500-10 for requests dated on or after 2025-04-01. So 10% is not the limit on this date.

**This is not approval authority:** the 15% shows what Acme is commercially eligible for. The exception says it "does not grant approval authority to any Northstar employee." The agreement also says each discount "remains subject to approval under Northstar's internal policies." A request at 15%, such as DR-9001 (submitted 2026-09-23, pending approval), still needs sign-off from whoever the discount policy names for that size of discount.

---

## A022 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

**Acme Manufacturing's maximum contractual discount on the NS-500 on 2026-09-23 is 15% of list price.**

That figure comes from the **Acme NS-500 Strategic Account Exception (EXC-ACME-NS500-15)**, which is Schedule B to agreement ACME-MFG-2025:

- **Customer:** Acme Manufacturing. The CRM account is CRM-2048. In the ERP the customer is "Acme Mfg. Holdings" (C-1001).
- **Product:** It covers only the NS-500 Industrial Controller (NS-500). It does not apply to any other Northstar product.
- **Maximum eligible discount:** 15% of list price.
- **Effective dates:** 2025-04-01 to 2028-03-31, so 2026-09-23 falls inside them.
- **Approval:** David Morgan approved it on 2025-03-20, Sarah Chen prepared it, and Deal Desk owns it.
- **Earlier exception:** It replaces **EXC-ACME-NS500-10** (the Acme NS-500 Volume Pricing Exception under ACME-SA-2023) for requests dated on or after 2025-04-01. That older record still shows "Active", but its terms don't govern a request on this date.

**Two caveats:**
1. The knowledge base doesn't record start or end dates for the parent agreement ACME-MFG-2025. The exception's own dates cover 2026-09-23, but I couldn't confirm from the parent agreement that the contract was active that day.
2. The exception says it "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." The 15% is the most Acme can receive. Any actual discount still needs approval from someone with enough authority under the discount policy in force.

---

## A023 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller is **15% off list price**.

**Where this comes from:**
- **Pricing exception EXC-ACME-NS500-15:** It names Acme Manufacturing as the customer and covers the "NS-500 Industrial Controller (NS-500) only." It says "Maximum eligible discount | 15% of list price." It runs from 2025-04-01 to 2028-03-31, so 2026-09-23 falls inside it. David Morgan, Chief Revenue Officer, approved it on 2025-03-20.
- **Master Supply Agreement:** This is between Northstar and Acme Mfg. Holdings, which trades as Acme Manufacturing. Section 3.2 says the customer "is eligible for discounts of up to **15%** on the NS-500 Industrial Controller, as set out in the pricing exception attached as Schedule B." The agreement runs from April 1, 2025 to March 31, 2028, so it was active on that date. I found nothing showing it was ended early under its Section 9.
- **The older 10% term no longer applies.** EXC-ACME-NS500-10, under agreement ACME-SA-2023, allowed up to 10% for orders from 2023-04-01 to 2025-03-31. EXC-ACME-NS500-15 replaces it for requests dated on or after 2025-04-01.

**Limits on the 15%:**
- It applies to the NS-500 only, not to any other Northstar product.
- The exception "establishes commercial eligibility only. It does not grant approval authority to any Northstar employee." Any actual discount request still needs approval from whoever has authority for that amount under the discount policy in effect at the time.

---

## A024 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

On 2022-10-01, I can't find any contractual NS-500 discount for Acme Manufacturing (CRM-2048 / ERP C-1001, "Acme Mfg. Holdings"). The two NS-500 pricing exceptions on file both start after that date:

| Exception | Agreement | Max discount | Covers |
|---|---|---|---|
| EXC-ACME-NS500-10 (Volume Pricing Exception, created 2023-03-12) | ACME-SA-2023 | 10% off list | Orders placed 2023-04-01 to 2025-03-31 |
| EXC-ACME-NS500-15 (Strategic Account Exception, Schedule B) | ACME-MFG-2025 (Master Supply Agreement) | 15% off list | 2025-04-01 to 2028-03-31; replaces the 10% exception for requests dated on or after 2025-04-01 |

The knowledge base has no Acme contract or exception covering NS-500 before 2023-04-01. That means 2022-10-01 falls under standard pricing, with no special terms. Neither later rate (10% or 15%) applies retroactively, because an exception only covers the dates it names.

If a discount request dated 2022-10-01 claims special contract terms, the document for those terms would have to be produced before anyone decides on it. Separately, any contractual rate only sets what the customer can get. It doesn't change who in the company has authority to approve the discount.

---

## A025 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 is **15% off list price**.

**Where this comes from:** Pricing exception **EXC-ACME-NS500-15**, the "Acme NS-500 Strategic Account Exception" (Schedule B to agreement ACME-MFG-2025).
- It names Acme Manufacturing as the customer and covers the NS-500 Industrial Controller **only**. It does not apply to any other Northstar product.
- It sets the maximum eligible discount at 15% of list price.
- It runs from 2025-04-01 to 2028-03-31, so it covers 2026-09-23.
- David Morgan, Chief Revenue Officer, approved it on 2025-03-20. Sarah Chen prepared it.

**The underlying contract is active on that date:** The Master Supply Agreement ACME-MFG-2025 is between Northstar and Acme Mfg. Holdings, which trades as Acme Manufacturing. It runs from April 1, 2025 to March 31, 2028. I found nothing showing it was terminated early.

**The older 10% exception doesn't apply:** EXC-ACME-NS500-10 under ACME-SA-2023 still says "Status: Active" in its own document. But it only covered orders placed from 2023-04-01 to 2025-03-31. The 15% exception also says it replaces the 10% one for requests dated on or after 2025-04-01.

**Other points:**
- This exception only sets what the customer is eligible for. It says it does not give any Northstar employee authority to approve a discount, so the approval limits in the discount policy still apply.
- Acme Manufacturing is CRM account CRM-2048 and ERP customer C-1001 (Acme Mfg. Holdings). It is not the same company as Acme Industrial Supply Co. (CRM-2091), which this exception doesn't cover.
- There is a pending request in CRM, DR-9001, for 15% off NS-500 dated 2026-09-23 and submitted by Sarah Chen. That is exactly the maximum. If you want an approval decision on it, I'd also need to check the policy in force that day and Sarah Chen's approval limit.

---

## A026 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can receive up to 15% off list price on the NS-500 because of a customer-specific pricing exception, **EXC-ACME-NS500-15** (titled "Acme NS-500 Strategic Account Exception"). That 15% is the most Acme can get, and the exception only makes Acme eligible for it. It doesn't approve any discount by itself.

**What the exception says** (source document 0501798b-359a-4b5a-a3ae-679b20711503):

| Term | Value | Quote |
|---|---|---|
| Contract it belongs to | Schedule B to agreement ACME-MFG-2025 | "Schedule B to agreement ACME-MFG-2025" |
| Customer | Acme Manufacturing | "Customer \| Acme Manufacturing" |
| Product | NS-500 only | "Product \| NS-500 Industrial Controller (NS-500) only"; "This exception applies only to the product identified above"; "It does not apply to any other Northstar product" |
| Maximum discount | 15% of list price | "Maximum eligible discount \| 15% of list price" |
| Dates | 2025-04-01 to 2028-03-31 | "Effective \| 2025-04-01"; "Expires \| 2028-03-31" |
| Replaces | EXC-ACME-NS500-10, for requests dated on or after 2025-04-01 | "Supersedes EXC-ACME-NS500-10" |
| Approved by | David Morgan, 2025-03-20 | "Exception approved by: David Morgan" |
| Prepared by / owner | Sarah Chen / Deal Desk | "Prepared by: Sarah Chen"; "owner: Deal Desk" |

**Which customer this is:** the exception names "Acme Manufacturing". That matches CRM account CRM-2048, which bills in ERP as "Acme Mfg. Holdings" (C-1001, D-U-N-S 04-812-7730). Acme Industrial Supply Co. (C-1044 / CRM-2091) is a different company, and the exception doesn't cover it.

**Limits to keep in mind:**
- **It doesn't give anyone approval authority.** The document says "This exception establishes commercial eligibility only" and "It does not grant approval authority to any Northstar employee." A specific 15% request still needs someone with enough authority under the discount policy in force on the request date. If the requestor's limit is below 15%, the approver the policy names for that discount level must sign off.
- **Only valid within its dates.** Requests dated from 2025-04-01 to 2028-03-31 fall under it. Earlier requests fall under the older exception, EXC-ACME-NS500-10, a "Volume Pricing Exception" under agreement ACME-SA-2023. The knowledge base doesn't record that older exception's maximum discount, though its ID suggests 10%.
- **Only the NS-500.** It doesn't apply to other products, such as NS-Cloud, which Acme is evaluating.
- **Gaps I couldn't fill:**
  - The knowledge base has no start date, end date or status for the parent agreement ACME-MFG-2025, so I couldn't confirm the contract itself is active on a given date.
  - The NS-500 shows up as several separate product records ("NS-500", "NS-500 controller", "NS-500 Industrial Controller (NS-500)"). They look like the same product, but none is tied to an SKU in the system of record, so I couldn't confirm the match by SKU.

Check both of those before approving a specific request.

---

## A027 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

**Short answer: there isn't one.** The knowledge base has no contract term or pricing exception that gives Acme Manufacturing a discount on the NS-500 on 2022-10-01. Every Acme NS-500 discount term I found starts later.

In the systems, Acme Manufacturing is CRM account CRM-2048 and ERP customer C-1001, billed as "Acme Mfg. Holdings". Its NS-500 discount terms, in order:

| Term | Max NS-500 discount | Valid for |
|---|---|---|
| EXC-ACME-NS500-10, the Volume Pricing Exception under agreement ACME-SA-2023 | 10% off list | Orders placed **2023-04-01 to 2025-03-31** |
| EXC-ACME-NS500-15, the Strategic Account Exception (Schedule B to agreement ACME-MFG-2025). It replaced the 10% exception for requests from 2025-04-01. | 15% off list, NS-500 only | **2025-04-01 to 2028-03-31** |
| Master Supply Agreement ACME-MFG-2025 | Up to 15% on the NS-500 (through Schedule B) | **2025-04-01 to 2028-03-31** |

2022-10-01 is six months before the earliest of these, the 10% exception. The record for agreement ACME-SA-2023 holds no dates or terms of its own, and I found no earlier Acme agreement. So on that date Acme had no contractual NS-500 discount: any discount would have been at standard pricing under the policy then in force. It's also worth noting that these exceptions only make the customer eligible for a discount. They don't give any employee authority to approve one.

If someone says an Acme contract term covered NS-500 discounts in 2022, ask for that document. The knowledge base doesn't have it.

---

## A028 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller was **10% off list price**.

**Where this comes from:**
- **The exception in force:** pricing exception **EXC-ACME-NS500-10**, under agreement **ACME-SA-2023**, says: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31."* 2024-10-01 falls inside that window.
- **Why it isn't 15%:** the 15% figure comes from **EXC-ACME-NS500-15**. It applies only to *"requests dated on or after 2025-04-01"* and runs to 2028-03-31. The new Master Supply Agreement it goes with also starts on April 1, 2025. Neither applied on 2024-10-01.

**Limits on the 10%:**
- It covers the NS-500 only, not other Northstar products.
- It only sets what Acme is commercially eligible for. It doesn't give any employee authority to approve a discount. A real request would still need an approver with enough authority under the discount policy in force on the request date.

---

## A029 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller was **10% off list price**.

**Where this comes from:**
- **Pricing exception EXC-ACME-NS500-10**, under agreement ACME-SA-2023, says: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31."* 2024-10-01 falls inside that period.
- **The later exception, EXC-ACME-NS500-15, doesn't apply yet on that date.** It allows up to 15% and runs from 2025-04-01 to 2028-03-31. It replaces the 10% exception only *"for requests dated on or after 2025-04-01."*

**Limits:**
- The exception covers the NS-500 only. It doesn't carry over to other Northstar products.
- The 15% exception says outright that it sets commercial eligibility only and gives no Northstar employee any approval authority. The same principle applies to the 10% one. Any request that uses this discount still needs approval from whoever holds that authority under the discount policy in force on the request date.

---

## A030 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off the NS-500 because its Master Supply Agreement says so, and a pricing exception attached to that agreement sets out the details. Both are in force today and run until 31 March 2028. That makes Acme eligible for the discount, but it doesn't approve any particular request.

**The evidence**

1. **Master Supply Agreement, ACME-MFG-2025** (`acme_master_supply_agreement.md`)
   - It's between Northstar Industrial Systems and Acme Mfg. Holdings, which trades as Acme Manufacturing.
   - §1 Term: it starts on 1 April 2025 and ends on 31 March 2028, unless either side ends it early for material breach (§9). I found no notice that it has been ended.
   - §3.2: *"Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller, as set out in the pricing exception attached as Schedule B."*
   - Signed by David Morgan (Northstar's Chief Revenue Officer) on 20 March 2025, and by Edward Floyd (Acme's VP Procurement) on 22 March 2025.

2. **Schedule B: the pricing exception, EXC-ACME-NS500-15** (`acme_pricing_exception.md`)
   - Customer: Acme Manufacturing. Product: *"NS-500 Industrial Controller (NS-500) only."*
   - The most it allows is **15% of list price**, from 1 April 2025 to 31 March 2028.
   - Scope: *"applies only to the product identified above. It does not apply to any other Northstar product."*
   - It replaces the older 10% exception (EXC-ACME-NS500-10 under ACME-SA-2023) for requests dated on or after 1 April 2025. The older document still says "Status: Active", but its own dates ended on 31 March 2025.

3. **Which customer this is.** Three records describe the same company, matched by name and the D-U-N-S number 04-812-7730:
   - the sales system (CRM) account "Acme Manufacturing" (CRM-2048)
   - the billing system (ERP) customer "Acme Mfg. Holdings" (C-1001)
   - the party named in the agreement.

**Limits to keep in mind**

- **The 15% is a maximum, not an approval.** §3.3 says: *"Customer's contractual pricing eligibility does not modify Northstar's internal approval authority. Each discount remains subject to approval under Northstar's internal policies."* Each request still needs approval from someone with enough authority under the discount policy in force at the time.
- **The NS-500 only.** The agreement also covers NS-Cloud and NS-Edge, but the 15% doesn't apply to them.
- **The account strategy note isn't evidence.** `acme_account_strategy.md` says "I believe it's 15%… Worth confirming with Deal Desk." That's someone's recollection; the agreement and Schedule B are what actually establish the 15%.
- **A request is pending now.** DR-9001 (Sarah Chen, 23 September 2026, 15% on a $250,000 NS-500 order) cites "Contract pricing per Acme Master Supply Agreement" and is waiting for approval. Acme is eligible for that 15%, but whether Sarah Chen can approve it herself or needs someone else depends on the discount policy, which I haven't checked here. I can work through that decision if you'd like.

---

## A031 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get **up to** 15% off list price on the NS-500 Industrial Controller because its current supply contract says so. The contract is reference ACME-MFG-2025, a Master Supply Agreement with Northstar Industrial Systems. Its Schedule B, the pricing exception EXC-ACME-NS500-15, sets the 15% limit. Both run from 2025-04-01 to 2028-03-31, so they are in force today (2026-10-18).

**Who the customer is.** Acme Manufacturing is the trading name ("doing business as") of Acme Mfg. Holdings. It is CRM account CRM-2048 and ERP customer C-1001, D-U-N-S number 04-812-7730, at 2200 N Industrial Pkwy, Milwaukee, WI. Don't confuse it with Acme Industrial Supply Co. (CRM-2091 / ERP C-1044), which is a different company.

**Evidence**
1. **Master Supply Agreement ACME-MFG-2025.** The parties are Northstar Industrial Systems and Acme Mfg. Holdings, doing business as Acme Manufacturing.
   - "This Agreement is effective April 1, 2025" and "expires March 31, 2028".
   - The NS-500 Industrial Controller (NS-500) is one of the products it covers.
   - "Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller", "as set out in the pricing exception attached as Schedule B".
   - Prices are "Northstar's current list prices… less any discount agreed in an Order".
2. **Schedule B: Acme NS-500 Strategic Account Exception (EXC-ACME-NS500-15).**
   - "Customer | Acme Manufacturing"; "Maximum eligible discount | 15% of list price".
   - "Product | NS-500 Industrial Controller (NS-500) only"; "It does not apply to any other Northstar product".
   - In effect from 2025-04-01 to 2028-03-31. Prepared by Sarah Chen, approved by David Morgan on 2025-03-20, owned by the Deal Desk.
   - "Supersedes EXC-ACME-NS500-10" for requests dated on or after 2025-04-01.
3. **Supporting, less formal sources.** The account notes say "Acme negotiated preferential NS-500 pricing in the 2025 agreement… it's 15%", and mention a 15% discount "approved for them last September". These agree with the contract, but the contract and Schedule B are what establish the eligibility.

**Limits on that eligibility**
- **15% is a maximum, not an automatic discount.** The agreement says "Each discount remains subject to approval under Northstar's internal policies". The exception adds: "This exception establishes commercial eligibility only. It does not grant approval authority to any Northstar employee." Any 15% request still needs sign-off from whoever the discount policy authorises at that level. Being eligible under the contract doesn't change that.
- **NS-500 only.** It doesn't cover NS-Cloud, NS-Edge or any other product, even though Acme is looking at NS-Cloud.
- **Old 10% exception.** The earlier exception (EXC-ACME-NS500-10, under agreement ACME-SA-2023) allowed only 10%, for orders placed from 2023-04-01 to 2025-03-31. Its record still says "Status: Active", but that's out of date: it has been replaced and its order period has ended. Anything dated before 2025-04-01 was capped at 10%, not 15%.

---

## A032 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 was **15% off list price**.

- **Where it comes from:** pricing exception EXC-ACME-NS500-15, the "Acme NS-500 Strategic Account Exception." It is Schedule B to agreement ACME-MFG-2025, and its stated maximum is "15% of list price."
- **Dates:** it runs from 2025-04-01 to 2028-03-31, so 2026-09-23 falls inside it. Sarah Chen prepared it, and David Morgan approved it on 2025-03-20.
- **Customer:** the exception names "Acme Manufacturing." That is CRM account CRM-2048, and its ERP bill-to record is "Acme Mfg. Holdings" (C-1001). Other Acme records, such as Acme Industrial Supply Co., are separate customers and aren't covered.
- **Product:** it covers only the "NS-500 Industrial Controller (NS-500)" and says it "does not apply to any other Northstar product." For example, it doesn't cover NS-Cloud, which Acme is evaluating.
- **The older 10% exception doesn't apply.** EXC-ACME-NS500-10 (under agreement ACME-SA-2023) gave up to 10% for orders placed from 2023-04-01 to 2025-03-31. EXC-ACME-NS500-15 replaces it for requests dated on or after 2025-04-01. The knowledge base still shows the old one as "Status: Active," but that label is out of date.

There are two limits on this answer:
- **Approval authority:** the exception says it "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." Any actual discount up to 15% still has to be approved under the discount policy in force on the request date.
- **Contract dates not checked:** the knowledge base doesn't hold start or end dates for the main agreement, ACME-MFG-2025. I could only confirm the exception's own dates, not that the contract itself was still active on 2026-09-23.

---

## A033 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller is **15% off list price**.

**Where this comes from:**
- **Pricing exception EXC-ACME-NS500-15** ("Acme NS-500 Strategic Account Exception", Schedule B to agreement ACME-MFG-2025) sets the "Maximum eligible discount" at "15% of list price". It covers the NS-500 only. It runs from 2025-04-01 to 2028-03-31, so it covers 2026-09-23. David Morgan, the Chief Revenue Officer, approved it on 2025-03-20.
- **The Master Supply Agreement (ACME-MFG-2025)** confirms it. Section 3.2 says Acme is "eligible for discounts of up to 15% on the NS-500 Industrial Controller, as set out in the pricing exception attached as Schedule B." The agreement also runs from 2025-04-01 to 2028-03-31. I found nothing showing it was ended early under Section 9.

**Not the 10% figure:** an older exception, EXC-ACME-NS500-10 under agreement ACME-SA-2023, allowed up to 10%. It still says "Status: Active", but it only covered orders from 2023-04-01 to 2025-03-31. EXC-ACME-NS500-15 also replaces it "for requests dated on or after 2025-04-01." So it doesn't apply on 2026-09-23.

**What the 15% doesn't cover:**
- **Approval:** the 15% only shows what Acme is commercially eligible for. It doesn't give any Northstar employee the authority to approve it. The exception says so directly, and MSA Section 3.3 says each discount still needs approval under Northstar's internal policies.
- **Other products:** the 15% doesn't apply to any other Northstar product, such as NS-CLOUD or NS-EDGE.

A 15% request for this date is still pending: DR-9001, logged by Sarah Chen on 2026-09-23. It's within Acme's eligibility, but it still needs approval from whoever the policy in force names for a 15% discount.

---

## A034 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing is eligible for up to 15% off the NS-500 Industrial Controller because two documents say so. One is its Master Supply Agreement with Northstar (ACME-MFG-2025). The other is a pricing exception attached to that agreement as Schedule B (EXC-ACME-NS500-15). Being eligible doesn't make a discount approved, though. Each discount still has to go through Northstar's normal approval process.

**Who the customer is**
The same company appears under different names in different systems:
- In the CRM it is account **CRM-2048**, "Acme Manufacturing" (Strategic tier, Midwest Enterprise).
- In the ERP it is customer **C-1001**, "Acme Mfg. Holdings", at 2200 N Industrial Pkwy, Milwaukee, WI 53209.
- Both records carry the same DUNS number, 04-812-7730. The agreement also names the company as "Acme Mfg. Holdings, doing business as Acme Manufacturing".

**Evidence 1: Master Supply Agreement (ACME-MFG-2025)**
- It is between Northstar Industrial Systems and Acme Mfg. Holdings. David Morgan (Chief Revenue Officer) signed for Northstar and Edward Floyd (VP Procurement) signed for Acme.
- It runs from April 1, 2025 to March 31, 2028, unless ended early under Section 9 (60 days' notice for material breach).
- The NS-500 is one of the products it covers.
- The discount clause: *"Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller."*
- Pricing is *"Northstar's current list prices… less any discount agreed in an Order."*

**Evidence 2: The NS-500 pricing exception (EXC-ACME-NS500-15, Schedule B to ACME-MFG-2025)**
- Customer: Acme Manufacturing. Product: *"NS-500 Industrial Controller (NS-500) only"*. It states *"It does not apply to any other Northstar product."*
- Maximum eligible discount: *"15% of list price."*
- Valid from 2025-04-01 to 2028-03-31.
- Approved by David Morgan on 2025-03-20, prepared by Sarah Chen, owned by the Deal Desk.
- It replaces the earlier exception, EXC-ACME-NS500-10, for requests dated on or after 2025-04-01. That earlier exception was presumably for 10%, judging by its name.

**Limits on that eligibility**
- **It covers the NS-500 only.** The agreement also covers NS-Cloud and the NS-Edge Monitoring Package, but the 15% exception doesn't extend to them.
- **The 15% is a ceiling.** Anything above 15% would need new or amended terms.
- **It doesn't grant approval authority.** The exception says it *"establishes commercial eligibility only"* and *"does not grant approval authority to any Northstar employee."* The agreement says *"Each discount remains subject to approval under Northstar's internal policies."*

**What this means for the pending request**
The open request is DR-9001: 15% on an NS-500 at a $250,000 list price ($37,500 off, net $212,500). Sarah Chen submitted it on 2026-09-23, citing "Contract pricing per Acme Master Supply Agreement", and its status is Pending Approval. That date falls within both documents' valid periods, so the eligibility holds. Who can approve it is a separate question: it depends on Sarah Chen's own limit and the approval bands in the discount policy in effect on that date. I haven't checked either here, and the contract can't be the only reason to approve it.

There is also an older document, the "Acme NS-500 Volume Pricing Exception" from 2023. It refers to an earlier agreement, ACME-SA-2023, and the knowledge base records no discount terms for it. It isn't the basis for the current 15%.

---

## A035 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing is eligible because of a **customer-specific pricing exception, EXC-ACME-NS500-15**. It allows up to 15% off list price on the NS-500 Industrial Controller, and it's in force today (2026-10-17).

**What the exception says** (all from the exception document):
- **Customer:** "| Customer | Acme Manufacturing |"
- **Product:** "| Product | NS-500 Industrial Controller (NS-500) only |". It also says: "It does not apply to any other Northstar product."
- **Maximum discount:** "| Maximum eligible discount | 15% of list price |"
- **Dates:** "| Effective | 2025-04-01 |" and "| Expires | 2028-03-31 |"
- **Approval:** "Exception approved by: David Morgan, Chief Revenue Officer, 2025-03-20." It was prepared by Sarah Chen, who owns the Acme account (CRM-2048).
- **What it replaced:** "Supersedes EXC-ACME-NS500-10 for requests dated on or after 2025-04-01."

**Supporting contract:** The Master Supply Agreement is between Northstar Industrial Systems and "Acme Mfg. Holdings, doing business as Acme Manufacturing." It "is effective April 1, 2025 and expires March 31, 2028, unless terminated earlier under Section 9." Those are the same dates as the exception. The knowledge base has nothing showing the agreement was terminated early.

**The earlier limit was 10%:** Under the earlier agreement ACME-SA-2023 and exception EXC-ACME-NS500-10, Acme "may receive up to 10% off list price on the NS-500… for orders placed from 2023-04-01 to 2025-03-31." So 15% only applies to requests dated on or after 2025-04-01. A request dated before then is capped at 10%.

**Limits on the 15% eligibility:**
- **It doesn't let anyone approve the discount.** The exception says: "This exception establishes commercial eligibility only. It does not grant approval authority to any Northstar employee." A 15% request still needs approval from someone whose authority under the discount policy in force covers 15%.
- **It covers the NS-500 only.** It doesn't carry over to other products.
- **It's a ceiling.** A request above 15% goes beyond Acme's eligibility, and a more senior approver can't fix that. It would need new or amended terms.

**Check before relying on the knowledge base:** One extracted fact says Northstar does business as Acme Manufacturing. That's a misreading of the agreement: the quoted text says Acme Mfg. Holdings does business as Acme Manufacturing.

---

## A036 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

CRM-2048 and C-1001 are the same customer. ACME-MFG-2025 appears in the knowledge base but isn't linked to any customer, so I can't confirm it. Acme Industrial Supply Co. is a different company.

**CRM-2048 (CRM) and C-1001 (ERP): Acme Mfg. Holdings, which trades as Acme Manufacturing**
- **CRM-2048** is the CRM account for Acme Manufacturing. It's a Strategic-tier account in the Midwest segment, owned by Sarah Chen, billed to 2200 N Industrial Pkwy, Milwaukee, WI, with DUNS 04-812-7730.
- **C-1001** is the ERP customer Acme Mfg. Holdings. It has the same address (Milwaukee, WI 53209), the same DUNS (04-812-7730) and Net 45 payment terms.
- **They're the same legal customer under two names.** The Master Supply Agreement names "Acme Mfg. Holdings, doing business as Acme Manufacturing" at that address. The guarantee document says the same, and adds that it is a wholly owned subsidiary of Acme Group Holdings, Inc. An account brief also lists "ERP bill-to: Acme Mfg. Holdings (C-1001)."

**ACME-MFG-2025: not confirmed**
The identifier exists in the knowledge base but has no facts or links to anything. Nothing in the knowledge base ties it to a customer, agreement or exception. Its name suggests it may be the reference for Acme Manufacturing's 2025 agreement. That would be the Master Supply Agreement, effective 2025-04-01 to 2028-03-31. But nothing confirms this. To be sure, check the agreement document itself.

**Acme Industrial Supply Co.: a different customer**
- **Its own records:** CRM-2091 (Standard tier, owned by Zachary Brown) and ERP C-1044. It's an industrial distributor at 17 Tallmadge Ave, Akron, OH 44310, with DUNS 09-552-1187. The address, DUNS, industry, tier and account owner all differ from Acme Manufacturing's.
- **The support agreement says so directly:** "Acme Industrial Supply Co. is a different company and is not covered."
- **Watch for "Acme Industrial":** at least one record uses this name for CRM-2091 (Acme Industrial Supply Co., Akron). Don't confuse it with Acme Manufacturing. Acme Manufacturing's terms don't apply to it, including the NS-500 pricing exception EXC-ACME-NS500-15 (up to 15%, 2025-04-01 to 2028-03-31).

---

## A037 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing can get **at most 15% off list price** on the NS-500 Industrial Controller.

**Where the 15% comes from:** pricing exception **EXC-ACME-NS500-15**.
- **Customer:** Acme Manufacturing (CRM-2048). Acme Manufacturing is the trading name of the legal entity Acme Mfg. Holdings.
- **Product:** the NS-500 Industrial Controller only. It "does not apply to any other Northstar product."
- **Maximum eligible discount:** "15% of list price."
- **Dates:** effective 2025-04-01, expires 2028-03-31, so 2026-09-23 falls inside it.
- **Approved by:** David Morgan, Chief Revenue Officer, on 2025-03-20.
- It replaced the earlier **EXC-ACME-NS500-10** (up to 10% off, for orders from 2023-04-01 to 2025-03-31) for requests dated on or after 2025-04-01. The old 10% cap therefore doesn't apply on that date.

**The contract:** the Acme Master Supply Agreement runs from April 1, 2025 to March 31, 2028, unless it is terminated earlier under its Section 9. It was in force on 2026-09-23, and the knowledge base records no termination.

**Two caveats:**
- The exception "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." A request for up to 15% still needs approval from whoever has authority for that discount level under the discount policy in force at the time.
- One internal message says Acme's 2025 pricing is "I believe it's 15%" and suggests checking with Deal Desk. That message isn't the source of this answer; the exception record above is.

---

## A038 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off list price on the NS-500 because of a signed agreement and a pricing exception attached to it. Both cover this product and both run until 31 March 2028. This makes Acme commercially eligible for the discount. It does not approve any particular discount.

**Who the customer is**
ACME Manufacturing is CRM account CRM-2048. In the ERP it is billed as "Acme Mfg. Holdings" (C-1001). Both records carry the same DUNS number, 04-812-7730, and the same Milwaukee address. It is a different company from Acme Industrial Supply Co. (CRM-2091 / C-1044), which these terms don't cover.

**The evidence**

1. **Master Supply Agreement ACME-MFG-2025**, between Northstar Industrial Systems and Acme Mfg. Holdings
   - It says: "Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller."
   - It runs from 1 April 2025 to 31 March 2028 ("This Agreement is effective April 1, 2025… expires March 31, 2028"). Either side can end it early for material breach, with 60 days' written notice.
   - David Morgan (Chief Revenue Officer) signed for Northstar and Edward Floyd (VP Procurement) signed for Acme.
   - It also says: "Each discount remains subject to approval under Northstar's internal policies."

2. **Pricing exception EXC-ACME-NS500-15** ("Acme NS-500 Strategic Account Exception"), Schedule B to ACME-MFG-2025
   - Customer: Acme Manufacturing. Product: "NS-500 Industrial Controller (NS-500) only." It "does not apply to any other Northstar product."
   - Maximum discount: "15% of list price."
   - It runs from 1 April 2025 to 31 March 2028.
   - Sarah Chen prepared it and David Morgan approved it on 20 March 2025. The Deal Desk owns it.
   - It replaces the earlier exception EXC-ACME-NS500-10 for requests dated on or after 1 April 2025.

**Older and weaker sources that don't support the 15%**
- **ACME-SA-2023 / the Volume Pricing Exception** gave up to **10%** on the NS-500, but only for orders from 1 April 2023 to 31 March 2025. That period is over and the 15% exception has replaced it. That document still shows "Status: Active", which should be cleaned up.
- **The Account Strategy 2026 note** only says "I believe it's 15%." That is someone's recollection, not proof. The figure is right only because the two documents above confirm it.

**Eligibility is not approval**
Both documents say this directly. The exception "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." The agreement makes each discount subject to Northstar's internal policies. So the open request DR-9001 (Sarah Chen, 23 September 2026, NS-500, 15% off $250,000, status "Pending Approval") still needs an approver with authority under the discount policy in force on that date. I haven't checked that policy or its approval levels here. If you want a decision on DR-9001, I can work through the full approval check.

---

## A039 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum contractual discount on the NS-500 is **15% of list price**.

1. **The contract is in force on that date.** The Master Supply Agreement (reference ACME-MFG-2025) runs from 2025-04-01 to 2028-03-31. It is between Northstar Industrial Systems and Acme Mfg. Holdings, which trades as Acme Manufacturing (CRM account CRM-2048, ERP customer C-1001). It says: "Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller".
2. **The pricing exception says the same.** Schedule B to that agreement is the exception EXC-ACME-NS500-15, the "Acme NS-500 Strategic Account Exception". It sets "Maximum eligible discount | 15% of list price", also from 2025-04-01 to 2028-03-31. It was approved by David Morgan (Chief Revenue Officer) on 2025-03-20.
3. **It covers only the NS-500.** The exception names "NS-500 Industrial Controller (NS-500) only" and "does not apply to any other Northstar product."
4. **It replaces the earlier exception.** EXC-ACME-NS500-15 "Supersedes EXC-ACME-NS500-10 for requests dated on or after 2025-04-01," so the older one does not apply on 2026-09-23. There is also an "Acme NS-500 Volume Pricing Exception" from 2023, tied to an older agreement (ACME-SA-2023). The knowledge base holds none of its terms or dates, and nothing shows it in force on 2026-09-23.

The 15% is only the most Acme is eligible for; it doesn't let anyone approve that discount. The exception says it "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." The agreement adds that each discount "remains subject to approval under Northstar's internal policies."

That matters for the request DR-9001: a 15% discount on NS-500 for Acme, dated 2026-09-23, raised by Sarah Chen and still "Pending Approval." It is within this maximum, but it still needs approval under the discount policy that was in force on that date.

---

## A040 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

I can't find any contractual NS-500 discount for Acme Manufacturing on 2022-10-01, so there's no contractual maximum to give. All the NS-500 discount terms on record start later:

| Term | Discount | Valid |
|---|---|---|
| Pricing exception EXC-ACME-NS500-10 (under agreement ACME-SA-2023) | Up to 10% off list price | Orders placed 2023-04-01 to 2025-03-31 |
| Pricing exception EXC-ACME-NS500-15 (Schedule B of the Master Supply Agreement) | Up to 15% off list price | 2025-04-01 to 2028-03-31 |
| Master Supply Agreement, §3.2 | Up to 15%, as set out in that exception | Agreement runs 2025-04-01 to 2028-03-31 |

Both exceptions name the customer as Acme Manufacturing. The Master Supply Agreement names Acme Mfg. Holdings, which trades as Acme Manufacturing (CRM-2048 / ERP C-1001). The exceptions cover the NS-500 only.

So on 2022-10-01 nothing found sets a contractual NS-500 discount for Acme. Any discount that day would be under standard pricing and the discount policy then in force. You also shouldn't apply the later 10% or 15% backwards, because a pricing exception only covers the dates it names.

One possible gap: the knowledge base doesn't record dates for agreement ACME-SA-2023 itself. Its 10% term only starts 2023-04-01, though, and nothing suggests Acme had a contract before then. If someone says there was a 2022 contract term, ask for the document before relying on it.

---

## A041 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

I can't find any contractual NS-500 discount for Acme Manufacturing on 2022-10-01. Neither of the two NS-500 pricing exceptions in the knowledge base had started by that date, so on what's recorded Acme was on standard pricing.

| Exception | Maximum discount | In force |
|---|---|---|
| EXC-ACME-NS500-10, under agreement ACME-SA-2023 | 10% off list | Orders placed 2023-04-01 to 2025-03-31 |
| EXC-ACME-NS500-15, alongside the Master Supply Agreement | 15% off list | 2025-04-01 to 2028-03-31; replaces the 10% exception for requests from 2025-04-01 |

Both exceptions cover the NS-500 Industrial Controller only. The 15% exception also says it sets commercial eligibility only and gives no Northstar employee authority to approve discounts. The Master Supply Agreement itself also runs only from April 1, 2025 to March 31, 2028.

The 15% figure also appears in an informal message ("I believe it's 15%…"). That's someone's belief, not a contract term, and it refers to the 2025 agreement anyway.

If someone says Acme had special NS-500 pricing in October 2022, it would have to come from a document I can't find. Ask them for that document rather than applying either the 10% or 15% figure.

---

## A042 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller was **10% off list price**.

**Where the 10% comes from**
- Agreement **ACME-SA-2023**, under pricing exception **EXC-ACME-NS500-10**, says: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31."* The agreement's status is shown as Active.
- 2024-10-01 falls inside that window.

**Why it isn't 15%**
- A newer exception, **EXC-ACME-NS500-15**, allows up to 15% off list. David Morgan, the Chief Revenue Officer, approved it on 2025-03-20. It only starts on **2025-04-01** and runs to 2028-03-31, and it replaces the 10% exception only "for requests dated on or after 2025-04-01."
- Acme's **Master Supply Agreement** also starts on April 1, 2025, so it doesn't apply on 2024-10-01 either.

Both exceptions cover only the NS-500, not other Northstar products. Also, the 10% is the most Acme is entitled to under the contract. It doesn't let any Northstar employee approve that discount. Who can approve still depends on the discount policy in force on the request date.

---

## A043 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 was **10% off list price**.

**Where this comes from:**
- **The Acme NS-500 Volume Pricing Exception** (owned by Deal Desk, created 2023-03-12) is attached to agreement **ACME-SA-2023**. It says: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31."* 2024-10-01 falls inside that window. The agreement's status is recorded as Active.
- **The later 15% exception doesn't apply to that date.** EXC-ACME-NS500-15 (the Strategic Account Exception, Schedule B to ACME-MFG-2025) raises the maximum to 15%. But it only takes effect on 2025-04-01 and runs to 2028-03-31. It replaces EXC-ACME-NS500-10 only "for requests dated on or after 2025-04-01," so it doesn't cover 2024-10-01.

**Notes:**
- The customer goes by several names. It is "Acme Manufacturing" in CRM (CRM-2048) and "Acme Mfg. Holdings" in ERP (C-1001), and the two records share DUNS number 04-812-7730.
- The exception it replaced, **EXC-ACME-NS500-10**, is probably the same 10% term under ACME-SA-2023. However, the knowledge base has no direct record linking the two, so this is an inference.
- This 10% is only what the customer could be offered. It doesn't give any employee the authority to approve a 10% discount; that still depends on the approval bands in the policy in force at the time.

---

## A044 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 was **10% off list price**.

**Where the 10% comes from:**
- It's set by the Acme NS-500 Volume Pricing Exception, **EXC-ACME-NS500-10**, under agreement **ACME-SA-2023**, owned by Deal Desk. Its status is Active.
- The wording is: *"Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500)… for orders placed from 2023-04-01 to 2025-03-31."* 2024-10-01 falls inside that window.
- The customer is the same one in both systems: CRM account CRM-2048 "Acme Manufacturing" and ERP customer C-1001 "Acme Mfg. Holdings", which does business as Acme Manufacturing.

**The 15% exception doesn't apply on that date:**
- The newer Strategic Account Exception, **EXC-ACME-NS500-15** (Schedule B to ACME-MFG-2025), allows up to 15%. But it only takes effect on 2025-04-01 and runs to 2028-03-31.
- It replaces the 10% exception only for requests dated on or after 2025-04-01, so it doesn't cover 2024-10-01.

**Two cautions:**
- An account note says Acme got 15% on NS-500 "last September." The knowledge base doesn't record when that note was written. If "last September" means September 2024, that discount was above Acme's 10% contractual limit at the time, so it shouldn't be used as a precedent for that period.
- Either exception only sets what Acme is eligible for. Neither gives any employee authority to approve a discount; that still goes through the approval bands in the discount policy.

---

## A045 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

On 2024-10-01, Acme Manufacturing's maximum contractual discount on the NS-500 Industrial Controller was **10% off list price**.

- **The term that applied:** the Acme NS-500 Volume Pricing Exception, created 2023-03-12, under agreement ACME-SA-2023. It says: "Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31." The agreement's status is recorded as Active. 2024-10-01 falls inside that window.
- **Why 15% doesn't apply on that date:** the newer Strategic Account Exception (EXC-ACME-NS500-15, Schedule B to ACME-MFG-2025) raises the maximum to 15% of list price. But it only takes effect on 2025-04-01 and runs to 2028-03-31. It replaces EXC-ACME-NS500-10 only "for requests dated on or after 2025-04-01," so it doesn't reach back to 2024-10-01.
- **The customer:** this is the account called Acme Manufacturing in CRM (CRM-2048) and Acme Mfg. Holdings in ERP (C-1001).

Two things to keep in mind:
- **The 10% is what the customer can get, not who can approve it.** Both exception documents give commercial eligibility only. The 15% exception says outright that it doesn't give any Northstar employee approval authority. A discount still needs approval under the policy that was in force at the time.
- **The older exception's ID is an inference.** The knowledge base doesn't directly link the 10% Volume Pricing Exception to the ID "EXC-ACME-NS500-10" that the 15% exception says it replaces. They appear to be the same document, but that isn't confirmed.

---

## A046 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

**I couldn't find a contractual maximum NS-500 discount for Acme Manufacturing on 2022-10-01.** Nothing in the knowledge base covers that date. The earliest Acme NS-500 pricing term starts six months later.

Acme Manufacturing is CRM account CRM-2048 and ERP customer C-1001, which appears in ERP as "Acme Mfg. Holdings". These are its NS-500 pricing terms:

| Source | Maximum NS-500 discount | Dates in force | Covers 2022-10-01? |
|---|---|---|---|
| ACME-SA-2023, via the "Acme NS-500 Volume Pricing Exception" (created 2023-03-12) | 10% off list | Orders placed 2023-04-01 to 2025-03-31 | No, starts later |
| Master Supply Agreement ACME-MFG-2025 | Up to 15% | 2025-04-01 to 2028-03-31 | No |
| Schedule B to ACME-MFG-2025 (exception EXC-ACME-NS500-15) | 15% of list | 2025-04-01 to 2028-03-31 | No |

Two loose ends:
- **EXC-ACME-NS500-10** appears only as the exception that EXC-ACME-NS500-15 replaced from 2025-04-01. The knowledge base doesn't hold its dates or terms. Its name suggests 10%, but nothing shows it covered 2022, so I can't treat it as the answer.
- **The account strategy note's "I believe it's 15%"** is about the 2025 agreement. It's an unverified recollection and doesn't apply to 2022.

On the evidence available, an NS-500 request dated 2022-10-01 would have been at standard pricing, with no contract term or exception on record. If someone says an older Acme agreement or the original NS500-10 exception applied then, that document would need to be produced.

---

## A047 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers point to the same customer: **Acme Mfg. Holdings, which does business as Acme Manufacturing**, headquartered at 2200 N Industrial Pkwy, Milwaukee, WI 53209 (D-U-N-S 04-812-7730). **Acme Industrial Supply Co. is a different company.**

**How each identifier connects**

| Identifier | System | What it is |
|---|---|---|
| CRM-2048 | CRM | The account record, under the name "Acme Manufacturing" (Strategic, Midwest Enterprise; owner Sarah Chen) |
| C-1001 | ERP | The bill-to customer, under the legal name "Acme Mfg. Holdings" (Net 45) |
| ACME-MFG-2025 | Contract | The agreement number. "Schedule B to agreement ACME-MFG-2025" (the Acme NS-500 Strategic Account Exception) and "Schedule C (Support and Service Levels) to ACME-MFG-2025" both name this customer |

The CRM and ERP names differ, but they are the same company. The Master Supply Agreement says "Acme Mfg. Holdings, doing business as Acme Manufacturing." The CRM and ERP records also share the same Milwaukee address and the same D-U-N-S number.

**Acme Industrial Supply Co. is not this customer**
- Schedule C says so outright: "Acme Industrial Supply Co. is a different company."
- It has its own records everywhere: ERP C-1044, CRM-2091, D-U-N-S 09-552-1187, at 17 Tallmadge Ave, Akron, OH 44310, in Industrial Distribution.
- None of Acme Manufacturing's contracts, exceptions or support terms apply to it. Schedule C also says its coverage does not extend to the parent company, Acme Group Holdings, Inc.

**Two things to watch for**
- Looking up CRM-2048 by itself in the knowledge base returns a service ticket (SR-39385), not the account. Looking up C-1001 the same way returns invoice INV-62011. Those documents mention the IDs; the actual customer record is Acme Manufacturing.
- The knowledge base holds Acme Industrial Supply Co. as two separate records, one from the CRM file and one from the ERP and contract documents. Both have the same D-U-N-S number, so they are the same company. A short name like "Acme" or "Acme Industrial" could mean either company, so confirm by CRM or ERP ID.

---

## A048 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off the NS-500 because its Master Supply Agreement (ACME-MFG-2025) says so, and the pricing exception attached to that agreement as Schedule B sets the same limit. That makes them commercially eligible. It does not approve any particular discount.

**Who the customer is**
- The CRM calls the account "Acme Manufacturing" (CRM-2048). The ERP calls it "Acme Mfg. Holdings" (C-1001). Both records give the same DUNS number (04-812-7730) and the same address, 2200 N Industrial Pkwy, Milwaukee.
- The agreement covers both names: it is made with "Acme Mfg. Holdings, doing business as Acme Manufacturing."

**The evidence**
1. **Master Supply Agreement — Acme** (`acme_master_supply_agreement.md`), reference ACME-MFG-2025
   - §1 Term: runs from 1 April 2025 to 31 March 2028. It can end early only for material breach, on 60 days' written notice (§9). I found nothing showing it has been terminated or amended.
   - §2 Products: the NS-500 Industrial Controller is one of the products it covers.
   - §3.2: *"Customer is eligible for discounts of up to **15%** on the NS-500 Industrial Controller, as set out in the pricing exception attached as Schedule B."*
   - Signed by David Morgan (Chief Revenue Officer) on 20 March 2025 and by Edward Floyd (Acme, VP Procurement) on 22 March 2025.
2. **Acme NS-500 Strategic Account Exception** (`acme_pricing_exception.md`), Schedule B to ACME-MFG-2025
   - Exception ID EXC-ACME-NS500-15. It covers Acme Manufacturing for the NS-500 *only*, with a maximum discount of 15% of list price.
   - It runs from 1 April 2025 to 31 March 2028.
   - Scope: *"applies only to the product identified above. It does not apply to any other Northstar product."*
   - Approved by David Morgan, CRO, on 20 March 2025.

**The older 10% exception**
- An older document, EXC-ACME-NS500-10 under agreement ACME-SA-2023 (`acme_pricing_exception_2023.md`), allowed up to 10%. It covered orders from 1 April 2023 to 31 March 2025.
- The new exception replaces it for requests dated on or after 1 April 2025.
- That older document still says "Status: Active," but its dates have passed and it has been replaced. Don't use it. Someone may want to correct that label.

**Limits on the eligibility**
- **It doesn't give anyone approval authority.** Agreement §3.3 says eligibility "does not modify Northstar's internal approval authority," and each discount still needs approval under internal policy. The exception says the same: it "establishes commercial eligibility only. It does not grant approval authority to any Northstar employee."
- **It covers the NS-500 only, and only until 31 March 2028.** It doesn't apply to NS-Cloud, NS-Edge or anything else.
- **A request is pending.** DR-9001 (Sarah Chen, 23 September 2026, 15% on NS-500, list price $250,000) is falling within these dates. It cites "Contract pricing per Acme Master Supply Agreement." Being eligible doesn't settle whether Sarah can approve 15% herself. That depends on the Sales Discount policy's approval limits, which I didn't check for this question.
- **The account strategy note is not evidence.** It says "I believe it's 15%… Worth confirming with Deal Desk." The signed agreement and Schedule B are what establish the 15%.

---

## A049 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers point to the same customer, **ACME Manufacturing**. **Acme Industrial Supply Co. is a different customer.**

**The three identifiers**

| Identifier | What it is | What the knowledge base shows |
|---|---|---|
| **CRM-2048** | CRM account number | The CRM record is "Acme Manufacturing", a Strategic account in Midwest Enterprise at 2200 N Industrial Pkwy, Milwaukee, WI. DUNS is 04-812-7730 and the account owner is Sarah Chen. |
| **C-1001** | ERP customer number | The ERP record is "Acme Mfg. Holdings" at the same address, with the same DUNS (04-812-7730), on Net 45 terms. The CRM record also lists "ERP bill-to: Acme Mfg. Holdings (C-1001)". |
| **ACME-MFG-2025** | An agreement number, not an account number | Two of its schedules name Acme Manufacturing as the customer: Schedule B, the "Acme NS-500 Strategic Account Exception", and Schedule C, "Support and Service Levels". |

The CRM and ERP names differ, but both identifiers resolve to the same entity: same address, same DUNS, and the CRM record names C-1001 directly. The knowledge base doesn't link ACME-MFG-2025 to Acme Manufacturing directly. That link comes only through Schedules B and C, which both name Acme Manufacturing as the customer.

**Acme Industrial Supply Co. is a different company**

- **It has its own identifiers:** CRM-2091 and ERP C-1044.
- **It has a different address:** 17 Tallmadge Ave, Akron, OH.
- **It has a different DUNS:** 09-552-1187.
- **Its account details differ:** it's a Standard tier account in Midwest Mid-Market, owned by Zachary Brown.
- **A document says so directly.** Schedule C states: *"Acme Industrial Supply Co. is a different company and is not covered."*

In practice, any terms under ACME-MFG-2025 apply only to ACME Manufacturing, such as the NS-500 Strategic Account Exception and the Schedule C support levels. They don't extend to Acme Industrial Supply Co. Schedule C also says it doesn't cover the parent company, Acme Group Holdings, Inc., or "Acme Mfg. Holdings affiliates".

---

## A050 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

I can't find any contractual maximum NS-500 discount for Acme Manufacturing on 2022-10-01. Every Acme pricing term in the knowledge base starts later than that date, so on the evidence available no contractual discount applied then.

Acme Manufacturing is the CRM account CRM-2048. In the ERP it's the customer "Acme Mfg. Holdings" (C-1001). These are its NS-500 pricing terms:

| Term | NS-500 maximum | Valid |
|---|---|---|
| ACME-SA-2023 (Acme NS-500 Volume Pricing Exception, created 2023-03-12) | 10% off list | 2023-04-01 to 2025-03-31 |
| Master Supply Agreement ACME-MFG-2025 | up to 15% | 2025-04-01 to 2028-03-31 |
| Schedule B exception EXC-ACME-NS500-15 (replaces EXC-ACME-NS500-10 for requests dated on or after 2025-04-01) | 15% of list | 2025-04-01 to 2028-03-31 |

- **The earliest term starts six months too late.** The 10% term begins on 2023-04-01.
- **One record is incomplete.** The knowledge base has no dates or terms for the older exception EXC-ACME-NS500-10. It is probably the 10% term under ACME-SA-2023, but nothing confirms that.
- **Before April 2023, standard pricing would apply.** If a 2022 order or request claimed contract pricing, ask for the contract or exception document first. Nothing here supports a contractual discount for that date.

---

## A051 · S07

**Question:** Why is Acme Manufacturing eligible for a 15% discount on the NS-500, and what is the evidence?

**Answer:**

Acme Manufacturing can get up to 15% off the NS-500 because of a signed pricing exception, **EXC-ACME-NS500-15**. The source is the exception document, not the contract itself.

**What the exception document says** (each point is quoted in the knowledge base):

| Term | Value |
|---|---|
| Customer | "Acme Manufacturing" |
| Product | "NS-500 Industrial Controller (NS-500) only". It "does not apply to any other Northstar product." |
| Maximum eligible discount | "15% of list price" |
| Effective | 2025-04-01 |
| Expires | 2028-03-31 |
| Supersedes | "EXC-ACME-NS500-10 for requests dated on or after 2025-04-01" |
| Approved by | "David Morgan, Chief Revenue Officer, 2025-03-20" |
| Prepared by | Sarah Chen (she is also the account owner in the CRM) |

So for a request dated today (2026-10-18), Acme can be offered up to 15% off the NS-500.

**Supporting context:**
- **The customer:** Acme Manufacturing is CRM account CRM-2048, a Strategic account in Milwaukee, WI. It is the trading name of Acme Mfg. Holdings, which signed the Master Supply Agreement.
- **The contract:** The Master Supply Agreement runs from April 1, 2025 to March 31, 2028, the same period as the exception. It is the active contract that goes with it.
- **The earlier terms:** Before that, the ACME-SA-2023 agreement and exception EXC-ACME-NS500-10 allowed up to 10% off the NS-500 for orders from 2023-04-01 to 2025-03-31. Requests dated before 2025-04-01 fall under that 10% cap.

**Caveats:**
1. **This doesn't decide who can approve it.** The exception says it "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." A 15% discount still has to be approved by whoever the discount policy in force at the time allows to approve that amount.
2. **It covers the NS-500 only.** It doesn't extend to other Northstar products.
3. **Don't rely on the email.** An internal email says "I believe it's 15%… worth confirming with Deal Desk." That is a guess, not evidence. It also credits the 15% to the 2025 agreement, but the knowledge base doesn't show the Master Supply Agreement stating a discount rate. The 15% comes from the exception document.

---

## A052 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers refer to one customer, **ACME Manufacturing**. **Acme Industrial Supply Co. is a different company.**

**The three identifiers**

| Identifier | System | What the records show |
|---|---|---|
| **CRM-2048** | CRM account | The CRM account list has "CRM-2048,Acme Manufacturing". Another record says "CRM account: CRM-2048". |
| **C-1001** | ERP customer (bill-to) | The ERP bill-to name is **Acme Mfg. Holdings**: "ERP bill-to: Acme Mfg. Holdings (C-1001)". The ERP customer row reads "C-1001, Acme Mfg. Holdings, Industrial Manufacturing, 2200 N Industrial Pkwy, Milwaukee, WI 53209, DUNS 04-812-7730, Net 45". |
| **ACME-MFG-2025** | The customer agreement | Two schedules are part of it, and both name ACME Manufacturing as the customer: Schedule B (the Acme NS-500 Strategic Account Exception) and Schedule C (Support and Service Levels). |

So "ACME Manufacturing" in CRM and "Acme Mfg. Holdings" in ERP are the same customer. DUNS number 04-812-7730 confirms it, and the account owner is Sarah Chen. Its parent company is Acme Group Holdings, Inc.

One thing that could mislead you: a direct lookup of CRM-2048 brings back service ticket SR-39385, and a lookup of C-1001 brings back invoice INV-62011. Those are just documents that mention the IDs. The customer record that holds both IDs is ACME Manufacturing.

**Acme Industrial Supply Co. is a separate customer**
- **Its own IDs:** CRM-2091, ERP C-1044 and DUNS 09-552-1187. It's an industrial distributor at 17 Tallmadge Ave, Akron, OH 44310, and its CRM contact is Zachary Brown.
- **The contract says so:** Schedule C to ACME-MFG-2025 states that "Acme Industrial Supply Co. is a different company and is not covered."

The knowledge base records that exclusion with a "no longer holds" flag, which wrongly suggests it was once covered. The quoted text simply says it is not covered.

ACME Manufacturing's contract terms, including the NS-500 exception and the support levels, don't apply to Acme Industrial Supply Co. Be careful with records that just say "Acme Industrial" or "Acme": "Acme Industrial" carries CRM-2091, so it points to the Akron company, not ACME Manufacturing.

---

## A053 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

On 2022-10-01, the knowledge base shows no contractual maximum NS-500 discount for Acme Manufacturing. No contract or pricing exception it holds covers that date, so Acme would have been on standard pricing then.

These are the only Acme NS-500 terms on record, and both start later:

| Term | Exception ID | Max NS-500 discount | Covers |
|---|---|---|---|
| Volume Pricing Exception (agreement ACME-SA-2023) | EXC-ACME-NS500-10 | 10% off list | Orders placed 2023-04-01 to 2025-03-31 |
| Strategic Account Exception (Schedule B to Master Supply Agreement ACME-MFG-2025) | EXC-ACME-NS500-15, replaced EXC-ACME-NS500-10 | 15% of list price | 2025-04-01 to 2028-03-31 |

The Master Supply Agreement also runs from 2025-04-01 to 2028-03-31. Neither term can be applied back to 2022-10-01, because an exception only covers the dates it names.

There are a few gaps:
- The knowledge base has no start or end date for agreement ACME-SA-2023 itself. Only the exception's order window (from 2023-04-01) is known.
- Nothing shows an Acme contract or exception in force in 2022.
- If someone says an earlier contract term applied on that date, ask for the document before relying on it.

Even where a discount is allowed under contract, it still needs approval under Northstar's internal discount policy.

---

## A054 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

**Answer: all three identifiers point to the same customer, ACME Manufacturing. Acme Industrial Supply Co. is a different company.**

**The three identifiers**

| Identifier | System | What it is |
|---|---|---|
| CRM-2048 | CRM | ACME Manufacturing's CRM account: "CRM account: CRM-2048 (Strategic, Midwest Enterprise)" and "CRM-2048,Acme Manufacturing" (crm_accounts.csv) |
| C-1001 | ERP | The ERP bill-to customer for the same company, recorded under its legal name: "ERP bill-to: Acme Mfg. Holdings (C-1001)" and "C-1001,Acme Mfg. Holdings,…Milwaukee,WI,53209,04-812-7730,Net 45" |
| ACME-MFG-2025 | Contract | The customer agreement for the same company. Schedule B (the NS-500 Strategic Account Exception) and Schedule C (Support and Service Levels) are both "to agreement ACME-MFG-2025", and both name Acme Manufacturing / Acme Mfg. Holdings as the customer. |

The CRM and ERP names differ, but they are one company. The contracts say "Acme Mfg. Holdings, doing business as Acme Manufacturing". Other details match too: both records carry DUNS 04-812-7730 and the address 2200 N Industrial Pkwy, Milwaukee, WI 53209. Acme Mfg. Holdings is a wholly owned subsidiary of Acme Group Holdings, Inc. Schedule C says its coverage does not extend to that parent.

**Acme Industrial Supply Co. is a separate customer.** Schedule C says so directly: "Acme Industrial Supply Co. is a different company." Its records don't match ACME Manufacturing's:
- ERP customer C-1044 and CRM account CRM-2091 (not C-1001 or CRM-2048)
- DUNS 09-552-1187 (not 04-812-7730)
- 17 Tallmadge Ave, Akron, OH 44310, in Industrial Distribution (not Milwaukee, Industrial Manufacturing)

So no ACME Manufacturing terms apply to Acme Industrial Supply Co., including the ACME-MFG-2025 agreement and its NS-500 pricing exception.

**Data issues in the knowledge base:**
- Looking up CRM-2048 and C-1001 by identifier returns the wrong records: a service ticket (SR-39385) and an invoice (INV-62011). Both IDs appear in those documents, but the correct match is the ACME Manufacturing record, where both IDs are recorded with evidence.
- Acme Industrial Supply Co. appears twice: once from ERP (C-1044) and once from CRM (CRM-2091). Both entries have the same DUNS, so they look like one company stored twice. They are not ACME Manufacturing.

---

## A055 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

All three identifiers point to one customer, and Acme Industrial Supply Co. is a different company.

**One customer: Acme Mfg. Holdings, which does business as Acme Manufacturing (Milwaukee, WI)**

| Identifier | System | What it is |
|---|---|---|
| **CRM-2048** | CRM | The account record "Acme Manufacturing": Strategic tier, Midwest Enterprise, 2200 N Industrial Pkwy, Milwaukee, WI. The owner is Sarah Chen. |
| **C-1001** | ERP | The customer record "Acme Mfg. Holdings", same address, Net 45 terms. Sales order SO-7001 is under this record. |
| **ACME-MFG-2025** | Agreement | The Master Supply Agreement between Northstar Industrial Systems and "Acme Mfg. Holdings, doing business as Acme Manufacturing", 2200 N Industrial Pkwy, Milwaukee, WI 53209. |

How these connect:
- The CRM and ERP records give the same DUNS number (04-812-7730) and the same address.
- The Account Strategy 2026 document lists both: "CRM account: CRM-2048" and "ERP bill-to: Acme Mfg. Holdings (C-1001)".
- The agreement covers the same legal entity. Its Schedule B is the NS-500 pricing exception EXC-ACME-NS500-15. Its Schedule C is the support schedule, which names the customer as Acme Mfg. Holdings, DUNS 04-812-7730.

**Acme Industrial Supply Co. is a separate customer.**
- **Its own records:** CRM-2091 (Standard tier, Midwest Mid-Market) and ERP C-1044.
- **Different details:** its DUNS number is 09-552-1187 and its address is 17 Tallmadge Ave, Akron, OH. Its account owner is Zachary Brown.
- **The agreement says so directly.** Schedule C to ACME-MFG-2025 states: *"Acme Industrial Supply Co. is a different company and is not covered."* It also says coverage doesn't extend to the parent company, Acme Group Holdings, Inc., or to any other affiliate.

Terms under ACME-MFG-2025, such as the 15% NS-500 pricing exception and Platinum support, apply only to Acme Mfg. Holdings / Acme Manufacturing (CRM-2048 / C-1001). They don't apply to Acme Industrial Supply Co.

---

## A056 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

**Answer:** CRM-2048 and C-1001 are the same customer. ACME-MFG-2025 probably belongs to that customer too, but I couldn't confirm it. Acme Industrial Supply Co. is a different company.

**The customer: Acme Mfg. Holdings, doing business as Acme Manufacturing**
- **CRM-2048** is the CRM account "Acme Manufacturing." It is a Strategic tier account in the Midwest segment, at 2200 N Industrial Pkwy, Milwaukee, WI, with DUNS 04-812-7730. Sarah Chen owns the account.
- **C-1001** is the ERP customer "Acme Mfg. Holdings," at the same Milwaukee address with the same DUNS 04-812-7730. Its payment terms are Net 45. An account note confirms the link: "ERP bill-to: Acme Mfg. Holdings (C-1001)".
- These are two names for one legal entity. The Master Supply Agreement is with "Acme Mfg. Holdings, doing business as Acme Manufacturing." The guarantee document describes Acme Mfg. Holdings as a wholly owned subsidiary of Acme Group Holdings, Inc.
- **ACME-MFG-2025** is in the knowledge base as an identifier, but nothing in it says what it identifies. The name suggests the 2025 Acme Manufacturing agreement: the Master Supply Agreement runs from 2025-04-01 to 2028-03-31, and pricing exception EXC-ACME-NS500-15 gives up to 15% off on the NS-500 controller. That is only an inference. Check the contract file before relying on that link.

**Acme Industrial Supply Co. is a separate customer**
- It has its own records: CRM-2091 (Standard tier, owned by Zachary Brown) and ERP C-1044.
- It is in Akron, OH (17 Tallmadge Ave) and has a different DUNS, 09-552-1187.
- A contract document says so directly: "Acme Industrial Supply Co. is a different company and is not covered." Acme Manufacturing's contract terms, including the NS-500 pricing exception, therefore don't apply to it.

**Watch out for a merged "Acme" record.** The knowledge base has a generic entity called "Acme" (also named "Acme Industrial") that mixes facts about both companies. It holds Acme Manufacturing details, such as being a strategic account standardised on the NS-500 and asking for 15% off, alongside a ticket for Acme Industrial at CRM-2091 in Akron. Don't use that record to decide which company something belongs to. Go by the account IDs, address and DUNS.

---

## A057 · S06b

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2024-10-01?

**Answer:**

I've found the two Acme NS-500 pricing exceptions and checked which one was in force on that date. Here's the answer.

**On 2024-10-01, Acme Manufacturing's maximum contractual NS-500 discount was 10% off list price.**

That comes from exception **EXC-ACME-NS500-10**, the "Acme NS-500 Volume Pricing Exception" under agreement ACME-SA-2023. It says: "Acme Manufacturing may receive up to **10%** off list price on the NS-500 Industrial Controller (NS-500) for orders placed from 2023-04-01 to 2025-03-31." 2024-10-01 falls inside that period.

**Why it isn't 15%:** The 15% figure comes from the later "Strategic Account Exception", **EXC-ACME-NS500-15**. That is Schedule B to agreement ACME-MFG-2025, and Section 3.2 of the Master Supply Agreement points to it. It runs from 2025-04-01 to 2028-03-31. It "Supersedes EXC-ACME-NS500-10 for requests dated on or after 2025-04-01", so it didn't apply in October 2024.

Some things to be aware of:
- **Stale status:** The 2023 exception document still says "Status: Active". Going by its own dates, it ended on 2025-03-31 and has since been replaced.
- **Not checked:** I couldn't find a start or end date for agreement ACME-SA-2023 itself. The 10% answer relies on the dates written in the exception.
- **Scope:** Both exceptions cover the NS-500 only. They set what the customer is eligible for, not who at Northstar can approve a discount. A request within 10% would still need sign-off under the internal discount policy.

ACME Manufacturing is CRM account CRM-2048, billed in the ERP as "Acme Mfg. Holdings" (C-1001).

---

## A058 · S06c

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2022-10-01?

**Answer:**

I checked every Acme contract and pricing exception in the knowledge base, and none of them covers 2022-10-01.

**On 2022-10-01, no contractual maximum discount on the NS-500 is on record for Acme Manufacturing.** That date is before every contract term and exception in the knowledge base:

| Terms | Maximum on NS-500 | Covers |
|---|---|---|
| ACME-SA-2023 (the "Acme NS-500 Volume Pricing Exception" document, created 2023-03-12) | 10% off list | Orders placed from 2023-04-01 to 2025-03-31 |
| Master Supply Agreement ACME-MFG-2025, Schedule B (exception EXC-ACME-NS500-15) | 15% of list | 2025-04-01 to 2028-03-31 |

- The earliest terms start on 2023-04-01, six months after the date you asked about.
- EXC-ACME-NS500-10 is an older exception that EXC-ACME-NS500-15 replaces from 2025-04-01. Its 10% figure probably matches the ACME-SA-2023 rate, but the knowledge base doesn't say. It records no start date, rate or terms for it, so nothing shows it applied in 2022.
- Without contract terms, a discount on that date would have fallen under standard pricing and the discount policy in force at the time.

If you need terms from 2022, ask Deal Desk, who own both exception documents, whether there was an earlier Acme agreement or exception. If there was one, it isn't in the knowledge base.

---

## A059 · S06a

**Question:** What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?

**Answer:**

On 2026-09-23, Acme Manufacturing's maximum NS-500 discount is **15% off list price**. This comes from pricing exception **EXC-ACME-NS500-15**.

- **Customer and product:** The exception covers Acme Manufacturing (CRM-2048). It applies only to the NS-500 Industrial Controller and no other Northstar product.
- **Dates:** It runs from 2025-04-01 to 2028-03-31, so it was in force on 2026-09-23.
- **Approval:** David Morgan, Chief Revenue Officer, approved it on 2025-03-20. Sarah Chen prepared it.
- **What it replaced:** It replaced EXC-ACME-NS500-10 for requests dated on or after 2025-04-01. That exception, under agreement ACME-SA-2023, allowed up to 10% for orders from 2023-04-01 to 2025-03-31, so the 10% cap no longer applies.

Strictly, the 15% comes from a pricing exception, not a clause in the contract itself. The exception says it "establishes commercial eligibility only" and "does not grant approval authority to any Northstar employee." Acme being eligible for up to 15% doesn't mean the person asking can approve it. Who can approve still depends on the discount policy in force at the time.

---

## A060 · S08

**Question:** Which customer do CRM-2048, C-1001 and ACME-MFG-2025 refer to — and is Acme Industrial Supply Co. the same customer?

**Answer:**

CRM-2048 and C-1001 refer to the same customer. ACME-MFG-2025 is in the knowledge base but isn't linked to any customer, so I can't confirm it. Acme Industrial Supply Co. is a different customer.

**CRM-2048 and C-1001: Acme Mfg. Holdings, doing business as Acme Manufacturing**
- **CRM-2048** is the CRM account "Acme Manufacturing": Strategic tier, Midwest, Industrial Manufacturing, 2200 N Industrial Pkwy, Milwaukee WI. The account owner is Sarah Chen and the DUNS number is 04-812-7730.
- **C-1001** is the ERP bill-to customer "Acme Mfg. Holdings": same address (Milwaukee WI 53209), same DUNS 04-812-7730, payment terms Net 45.
- The two systems use different names for one company. The Master Supply Agreement and the guarantee both say the customer is "Acme Mfg. Holdings, doing business as Acme Manufacturing," at 2200 N Industrial Pkwy, Milwaukee. Its parent and guarantor is Acme Group Holdings, Inc.

**ACME-MFG-2025: not confirmed**
- It exists as an entity, but nothing is recorded about it: no facts, no evidence and no links to other records. I can't confirm from the knowledge base which customer or document it refers to.
- It may be the reference number for Acme Manufacturing's 2025 Master Supply Agreement, which runs from April 1, 2025 to March 31, 2028. That is only a guess from the name, and nothing in the records links the two. Check the agreement document itself before relying on that.

**Acme Industrial Supply Co.: a different customer**
- Its records are CRM-2091 and ERP C-1044. It's a Standard-tier industrial distributor at 17 Tallmadge Ave, Akron OH 44310, with DUNS 09-552-1187, and its account owner is Zachary Brown.
- The DUNS number, address, industry, tier and account IDs all differ from Acme Manufacturing's.
- The support agreement with Acme Mfg. Holdings says so directly: "Acme Industrial Supply Co. is a different company and is not covered."
- So none of Acme Manufacturing's special terms apply to Acme Industrial Supply Co. That includes the NS-500 pricing exception EXC-ACME-NS500-15 (up to 15%, valid April 1, 2025 to March 31, 2028).
