# The systems-of-record database: schema and sample rows

One SQLite database (read-only) holding Northstar's exports from its CRM, ERP, HR system and service desk. Every value is as exported; an empty cell is NULL. Five sample rows per table (fewer where the table is smaller).

## `credit_requests` (11 rows)

| column | type |
|---|---|
| `request_id` | TEXT |
| `erp_customer_id` | TEXT |
| `current_limit_usd` | INTEGER |
| `requested_limit_usd` | INTEGER |
| `requested_by` | TEXT |
| `request_date` | TEXT |
| `justification` | TEXT |
| `status` | TEXT |
| `approved_by` | TEXT |
| `approved_on` | TEXT |

Sample rows:

| request_id | erp_customer_id | current_limit_usd | requested_limit_usd | requested_by | request_date | justification | status | approved_by | approved_on |
|---|---|---|---|---|---|---|---|---|---|
| CR-9201 | C-1001 | 250000 | 400000 | sarah.chen@northstar.example | 2026-09-23 | Third-plant ramp-up: higher NS-500 order volume through Q1 2027 | Pending Approval | NULL | NULL |
| CR-7001 | C-2008 | 150000 | 200000 | anthony.day@northstar.example | 2025-04-04 | Order growth | Approved | priya.shah@northstar.example | 2025-04-04 |
| CR-7002 | C-2001 | 150000 | 200000 | kelly.floyd@northstar.example | 2025-05-29 | Order growth | Approved | priya.shah@northstar.example | 2025-05-29 |
| CR-7003 | C-2008 | 200000 | 250000 | anthony.day@northstar.example | 2025-07-15 | Order growth | Approved | priya.shah@northstar.example | 2025-07-15 |
| CR-7004 | C-2008 | 250000 | 350000 | anthony.day@northstar.example | 2025-08-19 | Order growth | Declined | NULL | NULL |

## `crm_accounts` (12 rows)

| column | type |
|---|---|
| `account_id` | TEXT |
| `account_name` | TEXT |
| `account_tier` | TEXT |
| `segment` | TEXT |
| `industry` | TEXT |
| `billing_street` | TEXT |
| `billing_city` | TEXT |
| `billing_state` | TEXT |
| `duns_number` | TEXT |
| `account_owner` | TEXT |
| `owner_email` | TEXT |

Sample rows:

| account_id | account_name | account_tier | segment | industry | billing_street | billing_city | billing_state | duns_number | account_owner | owner_email |
|---|---|---|---|---|---|---|---|---|---|---|
| CRM-2048 | Acme Manufacturing | Strategic | Midwest Enterprise | Industrial Manufacturing | 2200 N Industrial Pkwy | Milwaukee | WI | 04-812-7730 | Sarah Chen | sarah.chen@northstar.example |
| CRM-2051 | BlueRiver Logistics | Standard | Central Enterprise | Logistics | 890 Harbor Way | St. Louis | MO | 07-331-9025 | Kelly Floyd | kelly.floyd@northstar.example |
| CRM-2063 | Cedar Health Systems | Standard | Central Enterprise | Healthcare | 51 Cedar Crest Blvd | Indianapolis | IN | 02-906-4418 | Anthony Day | anthony.day@northstar.example |
| CRM-2091 | Acme Industrial Supply Co. | Standard | Midwest Mid-Market | Industrial Distribution | 17 Tallmadge Ave | Akron | OH | 09-552-1187 | Zachary Brown | zachary.brown@northstar.example |
| CRM-3001 | Weiss Ltd | Standard | Central Enterprise | Chemicals | 906 Richardson Run | Madison | WI | 78-557-8304 | Kelly Floyd | kelly.floyd@northstar.example |

## `customers` (12 rows)

| column | type |
|---|---|
| `erp_customer_id` | TEXT |
| `customer_name` | TEXT |
| `industry` | TEXT |
| `bill_to_street` | TEXT |
| `bill_to_city` | TEXT |
| `bill_to_state` | TEXT |
| `bill_to_postal_code` | INTEGER |
| `duns_number` | TEXT |
| `payment_terms` | TEXT |

Sample rows:

| erp_customer_id | customer_name | industry | bill_to_street | bill_to_city | bill_to_state | bill_to_postal_code | duns_number | payment_terms |
|---|---|---|---|---|---|---|---|---|
| C-1001 | Acme Mfg. Holdings | Industrial Manufacturing | 2200 N Industrial Pkwy | Milwaukee | WI | 53209 | 04-812-7730 | Net 45 |
| C-1002 | Blue River Logistics LLC | Logistics | 890 Harbor Way | St. Louis | MO | 63102 | 07-331-9025 | Net 45 |
| C-1003 | Cedar Health Systems Inc. | Healthcare | 51 Cedar Crest Blvd | Indianapolis | IN | 46204 | 02-906-4418 | Net 45 |
| C-1044 | Acme Industrial Supply Co. | Industrial Distribution | 17 Tallmadge Ave | Akron | OH | 44310 | 09-552-1187 | Net 45 |
| C-2001 | Weiss Ltd Holdings | Chemicals | 906 Richardson Run | Madison | WI | 54721 | 78-557-8304 | Net 45 |

## `discount_requests` (26 rows)

| column | type |
|---|---|
| `request_id` | TEXT |
| `account_id` | TEXT |
| `product_sku` | TEXT |
| `requested_discount_pct` | REAL |
| `list_value_usd` | INTEGER |
| `discount_value_usd` | INTEGER |
| `net_value_usd` | INTEGER |
| `requested_by` | TEXT |
| `request_date` | TEXT |
| `justification` | TEXT |
| `status` | TEXT |
| `approved_by` | TEXT |
| `approved_on` | TEXT |

Sample rows:

| request_id | account_id | product_sku | requested_discount_pct | list_value_usd | discount_value_usd | net_value_usd | requested_by | request_date | justification | status | approved_by | approved_on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DR-7001 | CRM-3001 | NS-400-EQU | 5.0 | 9000 | 450 | 8550 | kelly.floyd@northstar.example | 2025-01-06 | Competitive | Approved | kelly.floyd@northstar.example | 2025-01-06 |
| DR-7002 | CRM-3007 | NS-EDGE | 8.0 | 85000 | 6800 | 78200 | anthony.day@northstar.example | 2025-01-09 | Competitive | Approved | anthony.day@northstar.example | 2025-01-09 |
| DR-7003 | CRM-3008 | NS-CLOUD | 10.0 | 120000 | 12000 | 108000 | anthony.day@northstar.example | 2025-02-15 | Competitive | Approved | anthony.day@northstar.example | 2025-02-15 |
| DR-7004 | CRM-3008 | NS-250-SOF | 18.0 | 308000 | 55440 | 252560 | anthony.day@northstar.example | 2025-04-27 | Competitive | Approved | michael.torres@northstar.example | 2025-04-27 |
| DR-7005 | CRM-2091 | NS-840-SER | 8.0 | 93000 | 7440 | 85560 | zachary.brown@northstar.example | 2025-05-04 | Competitive | Approved | zachary.brown@northstar.example | 2025-05-04 |

## `employees` (19 rows)

| column | type |
|---|---|
| `employee_id` | TEXT |
| `full_name` | TEXT |
| `preferred_name` | TEXT |
| `title` | TEXT |
| `department` | TEXT |
| `manager_id` | TEXT |
| `email` | TEXT |
| `location` | TEXT |

Sample rows:

| employee_id | full_name | preferred_name | title | department | manager_id | email | location |
|---|---|---|---|---|---|---|---|
| EMP-101 | Sarah Chen | NULL | Enterprise Account Executive | Sales | EMP-200 | sarah.chen@northstar.example | Chicago, IL |
| EMP-200 | Michael Torres | Mike | VP Sales | Sales | EMP-300 | michael.torres@northstar.example | Chicago, IL |
| EMP-300 | David Morgan | NULL | Chief Revenue Officer | Executive | NULL | david.morgan@northstar.example | Chicago, IL |
| EMP-401 | Priya Shah | NULL | Finance Manager | Finance | EMP-402 | priya.shah@northstar.example | Chicago, IL |
| EMP-402 | Elena Novak | NULL | Director of Finance | Finance | NULL | elena.novak@northstar.example | Chicago, IL |

## `erp_credit` (12 rows)

| column | type |
|---|---|
| `erp_customer_id` | TEXT |
| `credit_limit_usd` | INTEGER |
| `currency` | TEXT |
| `last_reviewed` | TEXT |

Sample rows:

| erp_customer_id | credit_limit_usd | currency | last_reviewed |
|---|---|---|---|
| C-1001 | 250000 | USD | 2026-01-15 |
| C-1002 | 100000 | USD | 2026-01-15 |
| C-1003 | 75000 | USD | 2026-01-15 |
| C-1044 | 50000 | USD | 2026-01-15 |
| C-2001 | 250000 | USD | 2025-12-31 |

## `erp_invoices` (30 rows)

| column | type |
|---|---|
| `invoice_id` | TEXT |
| `erp_customer_id` | TEXT |
| `invoice_date` | TEXT |
| `due_date` | TEXT |
| `amount_usd` | INTEGER |
| `paid_date` | TEXT |
| `reference` | TEXT |

Sample rows:

| invoice_id | erp_customer_id | invoice_date | due_date | amount_usd | paid_date | reference |
|---|---|---|---|---|---|---|
| INV-30001 | C-1044 | 2025-01-11 | 2025-02-25 | 343600 | 2025-03-04 | SO-5001 |
| INV-61005 | C-1002 | 2025-01-15 | 2025-03-01 | 30000 | 2025-02-26 | NS-CLOUD subscription 2025-Q1 |
| INV-30002 | C-2002 | 2025-02-16 | 2025-04-02 | 533900 | 2025-04-12 | SO-5003 |
| INV-30003 | C-1044 | 2025-03-23 | 2025-05-07 | 697100 | 2025-04-28 | SO-5005 |
| INV-30004 | C-2002 | 2025-04-14 | 2025-05-29 | 138900 | 2025-06-03 | SO-5006 |

## `erp_orders` (32 rows)

| column | type |
|---|---|
| `order_id` | TEXT |
| `erp_customer_id` | TEXT |
| `order_date` | TEXT |
| `order_value_usd` | INTEGER |
| `currency` | TEXT |
| `status` | TEXT |

Sample rows:

| order_id | erp_customer_id | order_date | order_value_usd | currency | status |
|---|---|---|---|---|---|
| SO-5001 | C-1044 | 2025-01-11 | 343600 | USD | Invoiced |
| SO-5002 | C-2004 | 2025-01-24 | 125400 | USD | Open |
| SO-5003 | C-2002 | 2025-02-16 | 533900 | USD | Invoiced |
| SO-5004 | C-2008 | 2025-03-21 | 698500 | USD | Open |
| SO-5005 | C-1044 | 2025-03-23 | 697100 | USD | Invoiced |

## `maintenance_notices` (1 rows)

| column | type |
|---|---|
| `notice_id` | TEXT |
| `account_id` | TEXT |
| `products` | TEXT |
| `sent_at` | TEXT |
| `window_start` | TEXT |
| `window_end` | TEXT |
| `notice` | TEXT |

Sample rows:

| notice_id | account_id | products | sent_at | window_start | window_end | notice |
|---|---|---|---|---|---|---|
| MN-2607 | CRM-2051 | NS-CLOUD | 2026-06-26T11:00:00-05:00 | 2026-07-11T22:00:00-05:00 | 2026-07-12T02:00:00-05:00 | NS-Cloud Operations Suite platform upgrade. |

## `products` (9 rows)

| column | type |
|---|---|
| `product_id` | TEXT |
| `sku` | TEXT |
| `product_name` | TEXT |
| `category` | TEXT |
| `list_price_usd` | INTEGER |

Sample rows:

| product_id | sku | product_name | category | list_price_usd |
|---|---|---|---|---|
| PROD-001 | NS-500 | NS-500 Industrial Controller | Equipment | 250000 |
| PROD-002 | NS-CLOUD | NS-Cloud Operations Suite | Software | 120000 |
| PROD-003 | NS-EDGE | NS-Edge Monitoring Package | Software | 85000 |
| PROD-101 | NS-250-SOF | NS-250 Safety Module | Software | 308000 |
| PROD-102 | NS-880-SER | NS-880 Commissioning Service | Service | 320000 |

## `service_credits` (2 rows)

| column | type |
|---|---|
| `credit_id` | TEXT |
| `ticket_id` | TEXT |
| `account_id` | TEXT |
| `ticket_opened` | TEXT |
| `amount_usd` | REAL |
| `approved_on` | TEXT |

Sample rows:

| credit_id | ticket_id | account_id | ticket_opened | amount_usd | approved_on |
|---|---|---|---|---|---|
| SCR-38655 | SR-38655 | CRM-2048 | 2026-03-04 | 3150.0 | 2026-04-02 |
| SCR-38790 | SR-38790 | CRM-2048 | 2026-03-19 | 420.0 | 2026-04-20 |

## `service_tickets` (10 rows)

| column | type |
|---|---|
| `ticket_id` | TEXT |
| `account_id` | TEXT |
| `customer_on_ticket` | TEXT |
| `site` | TEXT |
| `product_sku` | TEXT |
| `channel` | TEXT |
| `contact` | TEXT |
| `opened_at` | TEXT |
| `reported_priority` | TEXT |
| `description` | TEXT |
| `status` | TEXT |
| `restored_at` | TEXT |

Sample rows:

| ticket_id | account_id | customer_on_ticket | site | product_sku | channel | contact | opened_at | reported_priority | description | status | restored_at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SR-39385 | CRM-2048 | ACME Mfg — Milwaukee Plant 2 | Milwaukee Plant 2 | NS-500 | phone | Johnny Johnson, Director of Plant Operations | 2026-06-16T02:14:00-05:00 | P1 | NS-500 controller on stamping line 4 faulted with a hardware watchdog error at 01:58. Line 4 is stopped. No workaround. | Restored | 2026-06-16T10:58:00-05:00 |
| SR-39207 | CRM-2063 | Cedar Health | Fishers and Carmel outpatient centers | NS-CLOUD | portal | Cedar Health IT service desk | 2026-05-22T16:20:00-04:00 | P2 | NS-Cloud is unavailable to all users at our Fishers and Carmel outpatient centers (2 of our 14 facilities) since about 16:00. Facility operations at both centers are continuing. The other 12 facilities are working normally. | Restored | 2026-05-26T18:05:00-04:00 |
| SR-39561 | CRM-2051 | BlueRiver Logistics | St. Louis dispatch | NS-CLOUD | phone | BlueRiver night dispatch supervisor | 2026-07-11T23:20:00-05:00 | P1 | NS-Cloud has been down for all our users since about 23:10. Dispatch can't see any shipments. No workaround. | Restored | 2026-07-12T05:05:00-05:00 |
| SR-39340 | CRM-2063 | Cedar Health Systems Inc. | All facilities | NS-CLOUD | portal | Cedar Health IT service desk | 2026-06-10T07:05:00-04:00 | P3 | NS-Cloud won't load for anyone. None of our 14 facilities can see equipment status or alarms since about 06:15. Please look at it today. | Restored | 2026-06-10T12:35:00-04:00 |
| SR-39881 | CRM-2051 | Blue River Logistics LLC | St. Louis and Memphis depots | NS-CLOUD | portal | BlueRiver operations manager | 2026-08-20T19:45:00-05:00 | P2 | Since about 19:00, NS-Cloud shipment-exception alerts and route dashboards have stopped updating for our St. Louis and Memphis depots (2 of our 6). Dispatchers are phoning drivers to track exceptions. The other depots are fine. | Restored | 2026-08-24T10:40:00-05:00 |

## `ticket_events` (45 rows)

| column | type |
|---|---|
| `ticket_id` | TEXT |
| `at` | TEXT |
| `event` | TEXT |
| `actor` | TEXT |
| `detail` | TEXT |

Sample rows:

| ticket_id | at | event | actor | detail |
|---|---|---|---|---|
| SR-39385 | 2026-06-16T02:14:00-05:00 | created | Johnny Johnson, Director of Plant Operations | Ticket opened by phone; reported priority P1. |
| SR-39385 | 2026-06-16T02:31:00-05:00 | engineer_response | Northstar support engineer | A Northstar engineer phoned Johnny Johnson. |
| SR-39385 | 2026-06-16T10:58:00-05:00 | restored | Northstar support engineer | The failed controller was replaced with the on-site spare, and line 4 is running at full rate. |
| SR-39385 | 2026-06-24T10:12:00-05:00 | credit_claim | Edward Floyd | Credit claim received by email: Credit claim for SR-39385. |
| SR-39207 | 2026-05-22T16:20:00-04:00 | created | Cedar Health IT service desk | Ticket opened by portal; reported priority P2. |

