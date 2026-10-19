# Northstar systems-of-record database: schema notes, conventions and example queries

One read-only SQLite database holding Northstar's exports from its CRM, ERP, HR system and
service desk (Northstar Service). Every value is stored as exported; an empty cell is `NULL`.

This page describes what the database holds. The service-level rules themselves (severity,
targets, clocks, pauses, exclusions, credits, caps, claim windows, escalations) are in the
company documents listed at the end, not in the database. Several facts those rules depend on are
also **not** in the database. They are only in the documents: each customer's support plan,
covered products, coverage start and monthly support fee; the holiday calendar; and the holders of
the support escalation roles.

## Tables

### Service desk

**`service_tickets`**: one row per support ticket.

| column | meaning |
|---|---|
| `ticket_id` | Ticket number, `SR-nnnnn`. Primary identifier of a ticket. |
| `account_id` | CRM account the ticket belongs to → `crm_accounts.account_id`. |
| `customer_on_ticket` | Customer name as typed on the ticket. Free text; spellings vary (e.g. "ACME Mfg — …", "Cedar Health", "Blue River Logistics LLC"). Not an identifier. |
| `site` | Customer site(s) affected, free text. |
| `product_sku` | Product the ticket is about → `products.sku` (e.g. `NS-500`, `NS-CLOUD`). |
| `channel` | How the ticket was opened. Values seen: `phone`, `portal`. |
| `contact` | Customer contact who raised the ticket, free text. |
| `opened_at` | Open time, ISO 8601 with the UTC offset as recorded, e.g. `2026-06-16T02:14:00-05:00`. |
| `reported_priority` | The customer's reported priority, `P1`–`P4`. |
| `description` | The business impact as reported, free text. |
| `status` | Ticket status, e.g. `Restored`. |
| `restored_at` | Restoration time, same format as `opened_at`; `NULL` if not recorded. |

**`ticket_events`**: the event history of each ticket, one row per event. There is no event id.

| column | meaning |
|---|---|
| `ticket_id` | → `service_tickets.ticket_id`. |
| `at` | When the event happened, ISO 8601 with UTC offset. |
| `event` | Event type. Values seen in the samples: `created`, `engineer_response`, `restored`, `credit_claim`. These are not necessarily all the values; check with `SELECT DISTINCT event FROM ticket_events`. |
| `actor` | Who performed the event, as recorded: a customer contact, "Northstar support engineer", or a named person. |
| `detail` | Free-text note: what was said or done (e.g. "Ticket opened by phone; reported priority P1.", "Credit claim received by email: …"). |

**`maintenance_notices`**: scheduled-maintenance notices sent to customers.

| column | meaning |
|---|---|
| `notice_id` | Notice number, `MN-nnnn`. |
| `account_id` | CRM account notified → `crm_accounts.account_id`. |
| `products` | Product SKU(s) the notice names, stored as text (e.g. `NS-CLOUD`). |
| `sent_at` | When the notice was sent, ISO 8601 with offset. |
| `window_start`, `window_end` | Start and end of the maintenance window, ISO 8601 with offset. |
| `notice` | Notice text. |

**`service_credits`**: service credits already approved.

| column | meaning |
|---|---|
| `credit_id` | Credit id, `SCR-nnnnn`. |
| `ticket_id` | Ticket the credit is for → `service_tickets.ticket_id`. |
| `account_id` | CRM account → `crm_accounts.account_id`. |
| `ticket_opened` | Date the ticket was opened, `YYYY-MM-DD` (no time). |
| `amount_usd` | Credit amount in US dollars (REAL, e.g. `3150.0`). |
| `approved_on` | Approval date, `YYYY-MM-DD`. |

### CRM

**`crm_accounts`**: one row per CRM account.

| column | meaning |
|---|---|
| `account_id` | CRM account id, `CRM-nnnn`. |
| `account_name` | Account name in CRM. |
| `account_tier` | CRM account tier, e.g. `Strategic`, `Standard`. The support agreements state that the support plan is unrelated to the account tier. |
| `segment`, `industry` | Sales segment and industry. |
| `billing_street`, `billing_city`, `billing_state` | Billing address. |
| `duns_number` | DUNS number, `nn-nnn-nnnn`. |
| `account_owner` | Account owner's name, as recorded in CRM. |
| `owner_email` | Account owner's email → `employees.email`. |

**`discount_requests`**: sales discount requests (not used for support questions). `request_id`
(`DR-nnnn`), `account_id` (→ `crm_accounts`), `product_sku` (→ `products.sku`; some values carry a
suffix, e.g. `NS-400-EQU`), `requested_discount_pct` (percent, e.g. `8.0`), `list_value_usd`,
`discount_value_usd`, `net_value_usd`, `requested_by` and `approved_by` (employee emails),
`request_date`, `approved_on` (`YYYY-MM-DD`), `justification`, `status` (e.g. `Approved`).

### ERP

**`customers`**: one row per ERP customer. `erp_customer_id` (`C-nnnn`), `customer_name`
(the ERP/legal name, e.g. "Acme Mfg. Holdings"), `industry`, `bill_to_street`, `bill_to_city`,
`bill_to_state`, `bill_to_postal_code` (INTEGER), `duns_number` (`nn-nnn-nnnn`), `payment_terms`
(e.g. `Net 45`).

**`erp_invoices`**: `invoice_id` (`INV-nnnnn`), `erp_customer_id` (→ `customers`), `invoice_date`,
`due_date`, `paid_date` (`YYYY-MM-DD`; `paid_date` `NULL` if unpaid), `amount_usd` (INTEGER, US
dollars), `reference` (a sales order id `SO-nnnn` → `erp_orders.order_id`, or free text such as
"NS-CLOUD subscription 2025-Q1").

**`erp_orders`**: `order_id` (`SO-nnnn`), `erp_customer_id`, `order_date`, `order_value_usd`,
`currency` (`USD`), `status` (e.g. `Open`, `Invoiced`).

**`erp_credit`**: the customer's trade credit limit (financial credit, unrelated to service
credits). `erp_customer_id`, `credit_limit_usd`, `currency`, `last_reviewed`.

**`credit_requests`**: requests to raise a customer's trade credit limit (unrelated to service
credits). `request_id` (`CR-nnnn`), `erp_customer_id`, `current_limit_usd`, `requested_limit_usd`,
`requested_by`, `request_date`, `justification`, `status` (e.g. `Pending Approval`, `Approved`,
`Declined`), `approved_by`, `approved_on`.

**`products`**: product catalogue. `product_id` (`PROD-nnn`), `sku` (e.g. `NS-500`, `NS-CLOUD`,
`NS-EDGE`), `product_name` (e.g. "NS-Cloud Operations Suite"), `category` (`Equipment`, `Software`,
`Service`), `list_price_usd`.

### HR

**`employees`**: `employee_id` (`EMP-nnn`), `full_name`, `preferred_name` (`NULL` if none),
`title` (e.g. `VP Sales`, `Chief Revenue Officer`), `department`, `manager_id`
(→ `employees.employee_id`; `NULL` at the top), `email` (`first.last@northstar.example`),
`location`.

## How the tables relate

```
service_tickets.account_id ──► crm_accounts.account_id ◄── maintenance_notices.account_id
        │                               │                    service_credits.account_id
        │ ticket_id                     │ duns_number        discount_requests.account_id
        ▼                               ▼
ticket_events.ticket_id          customers.duns_number ──► erp_customer_id ──► erp_invoices,
service_credits.ticket_id                                                      erp_orders,
                                                                               erp_credit,
service_tickets.product_sku ──► products.sku                                   credit_requests
crm_accounts.owner_email    ──► employees.email
employees.manager_id        ──► employees.employee_id
```

- **CRM ↔ ERP.** No column stores a CRM account id next to an ERP customer id. Both tables carry
  `duns_number`, and that is the shared key. The names differ between systems (e.g. CRM
  "BlueRiver Logistics" vs ERP "Blue River Logistics LLC").
- **Identify customers by identifier, never by name.** The escalation procedure identifies a
  ticket's customer "by CRM account id, ERP customer id or DUNS, never by name alone". Names are
  ambiguous: "Acme Manufacturing" (CRM-2048) and "Acme Industrial Supply Co." (CRM-2091) are
  different companies with different DUNS numbers. The support agreements name the covered
  customer by legal name and DUNS.
- **Support agreements are not in the database.** To find a ticket's plan, covered products and
  monthly fee, match the account's DUNS to the DUNS stated in the agreement documents.

## Conventions

- **Timestamps** (`opened_at`, `restored_at`, `ticket_events.at`, `sent_at`, `window_start`,
  `window_end`) are ISO 8601 text with the UTC offset at which they were recorded. The offsets are
  not uniform: rows show `-05:00` and `-04:00`. The Service Level Schedules (§2.1) say all
  service-level times, deadlines and dates are in US Central Time (America/Chicago). A timestamp
  recorded in another zone is converted to CT before anything is measured, and "date" means the
  CT calendar date after conversion. CST is UTC−06:00 and CDT is UTC−05:00. The schedules say CDT
  applied from 2025-03-09 to 2025-11-02, and from 2026-03-08.
- **Comparing timestamps in SQL.** Text comparison of values with different offsets is not
  chronological. SQLite's `julianday()` / `datetime()` understand the `±HH:MM` suffix and
  normalise to UTC, so use `julianday(a) < julianday(b)` to compare instants. `date(x)` returns the
  **UTC** date, not the CT date.
- **Dates** without a time (`service_credits.ticket_opened`, `approved_on`, invoice and request
  dates, `erp_credit.last_reviewed`) are `YYYY-MM-DD` text.
- **Money** columns end in `_usd` and are US dollars. Most are INTEGER whole dollars.
  `service_credits.amount_usd` is REAL. `currency` columns hold `USD`.
- **Percentages** (`discount_requests.requested_discount_pct`) are stored as percent values
  (`8.0` = 8%).
- **Identifiers**: tickets `SR-nnnnn`, maintenance notices `MN-nnnn`, service credits
  `SCR-nnnnn`, CRM accounts `CRM-nnnn`, ERP customers `C-nnnn`, employees `EMP-nnn`, products
  `PROD-nnn`, invoices `INV-nnnnn`, sales orders `SO-nnnn`, DUNS `nn-nnn-nnnn`. The documents say
  every support request is a ticket in Northstar Service (`SR-nnnnn`), and notices are recorded
  there with an `MN-nnnn` number.
- **`reported_priority` is not severity.** The Support Severity Guide says the reported priority
  (P1–P4) "is only the customer's view: it does not set the severity". The database has no
  severity column. Severity is classified from the recorded impact (`description` and event notes).
- **`channel`** records how the ticket was opened. The Service Level Schedules treat a telephone
  report to the Support hotline differently from a portal submission or email (§6.3, §7.1).
- **Account owner** is "as recorded in Northstar CRM": `crm_accounts.account_owner` /
  `owner_email`.
- **Escalation role holders** (Support Escalation Manager, Director of Customer Support, Support
  Engineering Lead, Support Billing Manager, VP Sales, Chief Revenue Officer) are listed in the
  Support Organization document. Only some of them may appear in `employees`.
- **Holidays** are not in the database. The Northstar Holiday Calendar document is the complete
  list.
- **`NULL`** means the value was empty in the export, e.g. no restoration recorded or no approver.

## Example questions and SQL

Values in `?` are bound parameters.

**1. What does the record of a given ticket say, and which CRM account is it on?**
```sql
SELECT t.ticket_id, t.opened_at, t.channel, t.product_sku, t.reported_priority,
       t.description, t.status, t.restored_at,
       a.account_id, a.account_name, a.account_tier, a.duns_number
FROM service_tickets AS t
JOIN crm_accounts AS a ON a.account_id = t.account_id
WHERE t.ticket_id = ?;
```

**2. What is the event history of a ticket, in time order?**
```sql
SELECT at, event, actor, detail
FROM ticket_events
WHERE ticket_id = ?
ORDER BY julianday(at);
```

**3. Which ERP customer is a CRM account (matched by DUNS)?**
```sql
SELECT a.account_id, a.account_name, c.erp_customer_id, c.customer_name, c.duns_number
FROM crm_accounts AS a
JOIN customers AS c ON c.duns_number = a.duns_number
WHERE a.account_id = ?;
```

**4. Who is the account owner for a ticket's account, and who do they report to?**
```sql
SELECT a.account_owner, a.owner_email, e.employee_id, e.title,
       m.full_name AS manager_name, m.title AS manager_title
FROM service_tickets AS t
JOIN crm_accounts AS a ON a.account_id = t.account_id
LEFT JOIN employees AS e ON e.email = a.owner_email
LEFT JOIN employees AS m ON m.employee_id = e.manager_id
WHERE t.ticket_id = ?;
```

**5. Which service credits have already been approved for an account, in approval order?**
```sql
SELECT credit_id, ticket_id, ticket_opened, amount_usd, approved_on
FROM service_credits
WHERE account_id = ?
ORDER BY approved_on, credit_id;
```

**6. Which other tickets on the same account were opened around the same time as a given
ticket?** This returns the stored open times. Convert them to CT (see Conventions) before
assigning a calendar month.
```sql
SELECT o.ticket_id, o.opened_at, o.product_sku, o.status, o.restored_at
FROM service_tickets AS t
JOIN service_tickets AS o ON o.account_id = t.account_id
WHERE t.ticket_id = ?
ORDER BY julianday(o.opened_at);
```

**7. Is there a maintenance notice recorded for a ticket's account?**
```sql
SELECT n.notice_id, n.products, n.sent_at, n.window_start, n.window_end, n.notice
FROM service_tickets AS t
JOIN maintenance_notices AS n ON n.account_id = t.account_id
WHERE t.ticket_id = ?
ORDER BY julianday(n.window_start);
```

**8. Has a credit claim (or another given event type) been recorded on a ticket, and when?**
```sql
SELECT at, actor, detail
FROM ticket_events
WHERE ticket_id = ? AND event = ?      -- e.g. 'credit_claim'
ORDER BY julianday(at);
```

**9. Which employee holds a given title?**
```sql
SELECT employee_id, full_name, preferred_name, title, department, email
FROM employees
WHERE title = ?;                       -- e.g. 'VP Sales'
```

**10. Which CRM accounts and ERP customers carry a given DUNS number?**
```sql
SELECT account_id, account_name, account_tier FROM crm_accounts WHERE duns_number = ?;
SELECT erp_customer_id, customer_name FROM customers WHERE duns_number = ?;
```

## Source documents

- Northstar Support Service Level Schedule v1.0 (SLA-SCHEDULE-1.0) and v2.0 (SLA-SCHEDULE-2.0)
- Schedule C (Support and Service Levels): Acme Manufacturing (SUP-ACME-C)
- BlueRiver Logistics Support Terms (SUP-BRL-2025)
- Cedar Health Systems Support Terms (SUP-CHS-2025)
- Support Severity Guide (SUP-SEVERITY-GUIDE)
- Support Escalation Procedure (SOP-SUPPORT-007)
- Support Organization and Escalation Contacts (ORG-SUPPORT-2026)
- Northstar Holiday Calendar 2025–2026 (HR-HOLIDAYS-2025-26)
