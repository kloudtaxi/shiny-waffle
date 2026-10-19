# Systems-of-record database: schema notes and conventions

One SQLite database, read-only, holding Northstar's exports from four systems: the CRM, the ERP,
the HR system and the service desk (Northstar Service). Every value is as exported, and an empty
cell in the export is `NULL`. Nothing in the database has been converted, cleaned or reconciled
across systems. This page tells you what the tables mean, how they join, and what format each
value is in. Where a convention comes from a company document rather than from the data, the
document is cited.

## 1. Map of the tables

```
                         CRM                                   ERP
             crm_accounts.account_id (CRM-nnnn)     customers.erp_customer_id (C-nnnn)
                  |   duns_number  <---- same DUNS ---->  duns_number   |
                  |   owner_email                                       +--< erp_credit
                  |       |                                             +--< erp_invoices --reference--> erp_orders.order_id
     +------------+---------+-----------------+                         +--< erp_orders
     |            |         |                 |                         +--< credit_requests
     v            v         v                 v
service_tickets  service_  maintenance_  discount_requests
 .account_id     credits    notices        .account_id
     |           .account_id .account_id      |
     | ticket_id (SR-nnnnn)                   | product_sku
     +--< ticket_events.ticket_id             v
     +--< service_credits.ticket_id      products.sku  <--- service_tickets.product_sku
                                                           (also named in maintenance_notices.products)
                         HR
     employees.email  <--- crm_accounts.owner_email
     employees.manager_id ---> employees.employee_id
```

`A --< B` means one A row, many B rows. No table declares a primary or foreign key; the joins
above are by matching stored values.

## 2. Identifiers

| Identifier | Form (as stored) | Defined in | Referenced by |
|---|---|---|---|
| CRM account id | `CRM-nnnn` | `crm_accounts.account_id` | `service_tickets`, `service_credits`, `maintenance_notices`, `discount_requests` (all `account_id`) |
| ERP customer id | `C-nnnn` | `customers.erp_customer_id` | `erp_credit`, `erp_invoices`, `erp_orders`, `credit_requests` (all `erp_customer_id`) |
| DUNS number | `NN-NNN-NNNN`, with dashes | `crm_accounts.duns_number`, `customers.duns_number` | the support terms documents |
| Ticket number | `SR-nnnnn` | `service_tickets.ticket_id` | `ticket_events.ticket_id`, `service_credits.ticket_id` |
| Service credit id | `SCR-nnnnn` | `service_credits.credit_id` | |
| Maintenance notice number | `MN-nnnn` | `maintenance_notices.notice_id` | |
| Product SKU | e.g. `NS-500`, `NS-CLOUD`, `NS-250-SOF` | `products.sku` | `service_tickets.product_sku`, `discount_requests.product_sku`, `maintenance_notices.products` |
| Product id | `PROD-nnn` | `products.product_id` | nothing else in the database; join on `sku` |
| Employee id | `EMP-nnn` | `employees.employee_id` | `employees.manager_id` |
| Employee email | `first.last@northstar.example`, lower case | `employees.email` | `crm_accounts.owner_email`; `requested_by` and `approved_by` in `credit_requests` and `discount_requests` |
| Sales order | `SO-nnnn` | `erp_orders.order_id` | `erp_invoices.reference` (when it holds an order number) |
| Invoice | `INV-nnnnn` | `erp_invoices.invoice_id` | |
| Credit-limit request | `CR-nnnn` | `credit_requests.request_id` | |
| Discount request | `DR-nnnn` | `discount_requests.request_id` | |

Notes:

- **CRM and ERP use different customer ids.** The only column the CRM account and the ERP customer
  master both store is `duns_number`; there is no CRM-to-ERP cross-reference column. Join
  `crm_accounts` to `customers` on `duns_number`.
- **Names are not identifiers.** The same customer is named differently in each system: the CRM
  `account_name`, the ERP `customer_name` and the ticket's free-text `customer_on_ticket` differ
  (for example, in the samples, CRM "Acme Manufacturing", ERP "Acme Mfg. Holdings" and the ticket
  "ACME Mfg — Milwaukee Plant 2" share one DUNS). Different companies can have similar names. The
  Support Escalation Procedure says a ticket's customer is identified "by CRM account id, ERP
  customer id or DUNS, never by name alone".
- **The support terms documents identify the customer by legal name and DUNS**, and carry their
  own contract reference, which no column in the database stores:

  | Document | Reference | Customer (legal name) | DUNS |
  |---|---|---|---|
  | Schedule C (Support and Service Levels) — Acme Manufacturing | Schedule C to ACME-MFG-2025 | Acme Mfg. Holdings | 04-812-7730 |
  | BlueRiver Logistics Support Terms | SUP-BRL-2025 | Blue River Logistics LLC | 07-331-9025 |
  | Cedar Health Systems Support Terms | SUP-CHS-2025 | Cedar Health Systems Inc. | 02-906-4418 |

- `service_credits.credit_id`: in both sample rows the digits match the ticket's (SCR-38655 for
  SR-38655). Join on `ticket_id`, not on the id text.

## 3. Formats and units

**Timestamps** (`service_tickets.opened_at`, `service_tickets.restored_at`, `ticket_events.at`,
`maintenance_notices.sent_at`, `window_start`, `window_end`) are ISO 8601 text with seconds and a
numeric UTC offset: `YYYY-MM-DDTHH:MM:SS±HH:MM`, for example `2026-06-16T02:14:00-05:00`.

- The offset is whatever the source recorded. The samples carry both `-05:00` and `-04:00` (the
  two Cedar Health sample tickets are recorded at `-04:00`, the others at `-05:00`). The database
  does not convert anything to Central Time.
- The Service Level Schedule (v1.0 and v2.0, §2.1) states: all service-level times, business
  hours, deadlines and calendar dates are in US Central Time (America/Chicago), "CT"; Central
  Standard Time is UTC−06:00 and Central Daylight Time is UTC−05:00; CDT applied from 2025-03-09
  to 2025-11-02 and from 2026-03-08; a timestamp recorded in another zone (it names Eastern Daylight
  Time, UTC−04:00, and UTC in system logs) is converted to CT before anything is measured; and a
  "date" means the CT calendar date after conversion.
- **Comparing or sorting timestamp text is only chronological when both values have the same
  offset.** SQLite's date functions read the offset: `julianday('2026-06-16T02:14:00-05:00')`
  and `datetime(...)` return the UTC instant. SQLite has no America/Chicago rules, and the
  `localtime` modifier uses the host machine's zone, so it is not a CT conversion.
- Timestamps are whole minutes in every sample (seconds are `:00`).

**Dates** (`service_credits.ticket_opened`, `service_credits.approved_on`, `request_date`,
`approved_on`, `invoice_date`, `due_date`, `paid_date`, `order_date`, `last_reviewed`) are
`YYYY-MM-DD` text with no time or zone. Text order is date order.

**Money** is US dollars, in columns ending `_usd`. All are `INTEGER` whole dollars except
`service_credits.amount_usd`, which is `REAL` (dollars with cents, e.g. `3150.0`). The Service
Level Schedule (§6.5) says credits are "rounded to the nearest cent". `erp_credit.currency` and
`erp_orders.currency` hold `USD` in the samples.

**Percentages**: `discount_requests.requested_discount_pct` is `REAL` in percent (`5.0` means 5%).

**NULL** means the export cell was empty: no value was recorded. For example `restored_at` is NULL
when no restoration is recorded and `approved_by`/`approved_on` are NULL on requests not approved.

## 4. Tables

### Service desk (Northstar Service)

**`service_tickets`**: one row per support ticket. The SLA schedule (§2.5) says every support
request is a ticket in Northstar Service, numbered SR-nnnnn.

| Column | Meaning |
|---|---|
| `ticket_id` | Ticket number, `SR-nnnnn`. |
| `account_id` | The CRM account the ticket is logged against (`crm_accounts.account_id`). |
| `customer_on_ticket` | The customer name as typed on the ticket. Free text; varies from ticket to ticket. |
| `site` | The customer site(s) affected, free text. |
| `product_sku` | The product the ticket is about (`products.sku`). |
| `channel` | How the ticket was opened, as recorded. Sample values: `phone`, `portal`. |
| `contact` | The customer contact on the ticket (name and/or role), free text. |
| `opened_at` | Timestamp the ticket was opened (see §3 for format). |
| `reported_priority` | The priority the customer reported, `P1` to `P4`. The Support Severity Guide says this "is only the customer's view: it does not set the severity". |
| `description` | The reported problem and business impact, as recorded at opening. Free text. |
| `status` | Ticket status as exported. Sample value: `Restored`. |
| `restored_at` | Timestamp restoration was recorded, or NULL. |

There is **no severity column**. The Support Severity Guide says Northstar classifies severity
"from the business impact recorded in the ticket (its description and notes)".

**`ticket_events`**: the ticket's recorded history, one row per event. It is the only per-ticket
event history in the database; `service_tickets` holds only the ticket's current fields.

| Column | Meaning |
|---|---|
| `ticket_id` | Ticket number (`service_tickets.ticket_id`). |
| `at` | Timestamp the event was recorded (see §3). |
| `event` | Event type as stored. Sample values: `created`, `engineer_response`, `restored`, `credit_claim`. Other values may exist; list them with example 8 below. |
| `actor` | Who acted, free text: a customer contact, "Northstar support engineer", or a person's name. |
| `detail` | Free text describing the event (e.g. "Ticket opened by phone; reported priority P1."). |

There is no event id; a ticket's events are its rows with that `ticket_id`.

**`service_credits`**: service credits already approved, one row per credit.

| Column | Meaning |
|---|---|
| `credit_id` | Credit id, `SCR-nnnnn`. |
| `ticket_id` | The ticket the credit was approved for. |
| `account_id` | The CRM account. |
| `ticket_opened` | The ticket's open date as stored (`YYYY-MM-DD`). |
| `amount_usd` | Credit amount in US dollars (`REAL`). |
| `approved_on` | Date the credit was approved (`YYYY-MM-DD`). |

**`maintenance_notices`**: maintenance notices sent to customers. The SLA schedule (§5.1) says
notices are recorded in Northstar Service with an MN-nnnn number.

| Column | Meaning |
|---|---|
| `notice_id` | Notice number, `MN-nnnn`. |
| `account_id` | The CRM account the notice was sent to. |
| `products` | The product SKU(s) the notice names, as text. The sample holds one SKU; the separator for several is not shown in the samples. |
| `sent_at` | Timestamp the notice was sent. |
| `window_start`, `window_end` | Start and end of the maintenance window (timestamps). |
| `notice` | The notice text. |

### CRM

**`crm_accounts`**: one row per CRM account.

| Column | Meaning |
|---|---|
| `account_id` | CRM account id, `CRM-nnnn`. |
| `account_name` | Account name in the CRM. |
| `account_tier` | CRM account tier. Sample values: `Strategic`, `Standard`. The support terms say the support plan "is unrelated to the Customer's account tier". |
| `segment`, `industry` | CRM segment and industry. |
| `billing_street`, `billing_city`, `billing_state` | Billing address. |
| `duns_number` | DUNS number, `NN-NNN-NNNN`. |
| `account_owner` | Account owner's name. The Support Escalation Procedure and the support org chart refer to the account owner "as recorded in Northstar CRM". |
| `owner_email` | Account owner's email; matches `employees.email`. |

**`discount_requests`**: sales discount requests (not about support). `account_id` (CRM),
`product_sku`, `requested_discount_pct` (percent), `list_value_usd`, `discount_value_usd`,
`net_value_usd`, `requested_by` and `approved_by` (employee emails), `request_date` and
`approved_on` (dates), `justification`, `status` (sample: `Approved`).

### ERP

**`customers`**: the ERP customer master. `erp_customer_id` (`C-nnnn`), `customer_name` (ERP
name, often the legal name), `industry`, `bill_to_street`, `bill_to_city`, `bill_to_state`,
`bill_to_postal_code` (stored as `INTEGER`), `duns_number`, `payment_terms` (e.g. `Net 45`).

**`erp_credit`**: one row per ERP customer: `credit_limit_usd`, `currency`, `last_reviewed` (date).
**`credit_requests`**: requests to change a customer's credit limit: `current_limit_usd`,
`requested_limit_usd`, `requested_by`, `request_date`, `justification`, `status` (samples:
`Pending Approval`, `Approved`, `Declined`), `approved_by`, `approved_on`.
**`erp_orders`**: sales orders: `order_id` (`SO-nnnn`), `order_date`, `order_value_usd`,
`currency`, `status` (samples: `Open`, `Invoiced`).
**`erp_invoices`**: invoices: `invoice_id`, `invoice_date`, `due_date`, `amount_usd`, `paid_date`
(NULL if unpaid), `reference` (a sales order number, or a text label such as a subscription
period).

These four ERP tables are about credit and sales, not support.

### HR

**`employees`**: one row per employee.

| Column | Meaning |
|---|---|
| `employee_id` | Employee id, `EMP-nnn`. |
| `full_name` | Full name. |
| `preferred_name` | Preferred name, or NULL if none is recorded (sample: `Mike` for Michael Torres). |
| `title` | Job title (e.g. `VP Sales`, `Chief Revenue Officer`). |
| `department` | Department. |
| `manager_id` | The manager's `employee_id`, or NULL. |
| `email` | Work email, `first.last@northstar.example`. |
| `location` | Office, `City, ST`. |

Email is the value shared by `employees`, `crm_accounts.owner_email` and the support org chart
document; names can appear in different forms (`full_name`, `preferred_name`).

## 5. What the database does not hold

These are in company documents, not in any table:

| Information | Where it is |
|---|---|
| Support plan (Platinum, Silver), covered products, coverage start and monthly support fee, per customer | Each customer's support terms (table in §2 above) |
| Response and restoration targets, clocks, pauses, exclusions, credit percentages, cap, claim window | Northstar Support Service Level Schedule v1.0 and v2.0; §1 of each says which tickets it applies to |
| Severity definitions | Support Severity Guide |
| Who is engaged or notified, and when | Support Escalation Procedure |
| Holders of the support roles (Support Escalation Manager, Director of Customer Support, Support Engineering Lead, Support Billing Manager) and of VP Sales and Chief Revenue Officer, with emails | Support Organization and Escalation Contacts |
| Northstar holidays | Northstar Holiday Calendar, 2025–2026 |

## 6. Example queries

Placeholders such as `:ticket_id` stand for the value you supply.

**1. What is recorded on a ticket, with the account it is logged against?**

```sql
SELECT t.ticket_id, t.opened_at, t.channel, t.reported_priority, t.product_sku,
       t.description, t.status, t.restored_at,
       a.account_id, a.account_name, a.account_tier, a.duns_number,
       a.account_owner, a.owner_email
FROM service_tickets AS t
JOIN crm_accounts AS a ON a.account_id = t.account_id
WHERE t.ticket_id = :ticket_id;
```

**2. What is a ticket's recorded history, in time order?**

`at` values can carry different offsets, so order by the instant, not the text.

```sql
SELECT at, event, actor, detail
FROM ticket_events
WHERE ticket_id = :ticket_id
ORDER BY julianday(at), rowid;
```

**3. Which ERP customer is a ticket's customer?**

```sql
SELECT t.ticket_id, a.account_id, a.account_name, a.duns_number,
       c.erp_customer_id, c.customer_name
FROM service_tickets AS t
JOIN crm_accounts AS a ON a.account_id = t.account_id
LEFT JOIN customers AS c ON c.duns_number = a.duns_number
WHERE t.ticket_id = :ticket_id;
```

A NULL `erp_customer_id` means no ERP customer has that DUNS; more than one row means several do.

**4. Which CRM account and ERP customer does a document's DUNS number refer to?**

```sql
SELECT a.account_id, a.account_name, c.erp_customer_id, c.customer_name, a.duns_number
FROM crm_accounts AS a
LEFT JOIN customers AS c ON c.duns_number = a.duns_number
WHERE a.duns_number = :duns_number;
```

**5. Which service credits have already been approved for a customer, in approval order?**

```sql
SELECT credit_id, ticket_id, ticket_opened, amount_usd, approved_on
FROM service_credits
WHERE account_id = :account_id
ORDER BY approved_on, rowid;
```

**6. Which maintenance notices are on record for a ticket's account?**

```sql
SELECT n.notice_id, n.products, n.sent_at, n.window_start, n.window_end, n.notice,
       t.product_sku, t.opened_at
FROM service_tickets AS t
JOIN maintenance_notices AS n ON n.account_id = t.account_id
WHERE t.ticket_id = :ticket_id;
```

**7. Who owns a ticket's account in the CRM, and who is that person's manager?**

```sql
SELECT a.account_owner, a.owner_email,
       e.employee_id, e.title, e.department,
       m.employee_id AS manager_id, m.full_name AS manager_name,
       m.title AS manager_title, m.email AS manager_email
FROM service_tickets AS t
JOIN crm_accounts AS a ON a.account_id = t.account_id
LEFT JOIN employees AS e ON e.email = a.owner_email
LEFT JOIN employees AS m ON m.employee_id = e.manager_id
WHERE t.ticket_id = :ticket_id;
```

**8. Which event types does the ticket history use, and how often?**

```sql
SELECT event, COUNT(*) AS n
FROM ticket_events
GROUP BY event
ORDER BY event;
```

**9. Has a credit claim been recorded on a ticket, and when?**

```sql
SELECT at, actor, detail
FROM ticket_events
WHERE ticket_id = :ticket_id
  AND event = 'credit_claim'
ORDER BY julianday(at), rowid;
```

**10. Which other tickets has the same customer opened, and on which products?**

```sql
SELECT o.ticket_id, o.opened_at, o.product_sku, p.product_name, o.status, o.restored_at
FROM service_tickets AS t
JOIN service_tickets AS o ON o.account_id = t.account_id
LEFT JOIN products AS p ON p.sku = o.product_sku
WHERE t.ticket_id = :ticket_id
ORDER BY julianday(o.opened_at), o.rowid;
```
