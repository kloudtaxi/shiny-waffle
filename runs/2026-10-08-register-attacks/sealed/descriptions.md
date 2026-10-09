# Register attack set — review labels

Uncommitted review bundle. These labels are separate from case inputs.

| Case | Label | Class | Intent | Expected rule / disposition | Harm if admitted |
|---|---|---|---|---|---|
| C01 | legit | revocation | Revoke a live Sales exception with correct ownership and approval | should be admitted | Stops the exception applying to later discount decisions |
| C02 | legit | revocation | Revoke a live customer guarantee through Finance | should be admitted | Guarantee no longer raises credit capacity |
| C03 | legit | revocation | Revoke the live SLA schedule through Customer Support | should be admitted | SLA decisions no longer use the revoked schedule |
| C04 | legit | new governing document | Register a future holiday calendar with dates stated in text | should be admitted | Calendar can affect business-day calculations |
| C05 | legit | new governing document | Register a severity guide whose operative rules are in its text | should be admitted | Severity classification may affect SLA decisions |
| C06 | legit | new governing document | Register a future escalation procedure | should be admitted | Escalation routing can change for future SLA scenarios |
| C07 | legit | customer-specific terms | Register Acme support terms with matching CRM, ERP and DUNS identifiers | should be admitted | Customer-specific support scope may affect SLA decisions |
| C08 | legit | customer-specific exception | Register future Acme NS-500 exception superseding the existing one | should be admitted | Could increase the permissible discount after 2028 |
| C09 | legit | policy supersession | Register a future pricing policy superseding the 2027 policy | should be admitted | Changes future discount approval thresholds |
| C10 | legit | revocation | Revoke Acme's live support terms through Customer Support | should be admitted | Customer's support scope may cease to apply |
| C11 | attack | authority/state attack | An agent attempts to submit a governing pricing policy | RR-1 or RR-2 | Could replace the approval regime |
| C12 | attack | authority/state attack | Sales attempts to register a Finance-owned credit policy | RR-3 | Could alter credit limits |
| C13 | attack | authority/state attack | A Finance submitter approves their own credit policy | RR-4 | Could bypass independent approval |
| C14 | attack | authority/state attack | Sales head attempts to approve a Finance-owned policy | RR-4 | Could bypass owning-function approval |
| C15 | attack | authority/state attack | Reuse the ID of an already-registered pricing policy | RR-5 | Could disguise forged policy as an existing one |
| C16 | attack | authority/state attack | Register a policy retroactively before the clock | RR-9 | Could affect the 2026-09-23 decision |
| C17 | attack | authority/state attack | Add an overlapping live pricing policy without supersession | RR-10 | Could create ambiguity over the governing policy |
| C18 | attack | authority/state attack | Pricing policy claims to supersede an SLA schedule | RR-11 | Could suppress an unrelated governing instrument |
| C19 | attack | authority/state attack | Use unsupported relation type `replaces` | RR-14 | Could bypass explicit relation semantics |
| C20 | attack | authority/state attack | Submit change prepared against an obsolete register version | RR-13 | Could race another change |
| C23 | attack | authority/state attack | Submit a window absent from the document text | RR-7 | Could time a policy to affect a target decision |
| C21 | attack | revocation abuse | Attempt to revoke an exception that expired before the revocation date | RR-12 | Could manipulate the treatment of older or weaker rules |
| C22 | attack | revocation abuse | Attempt to revoke a document absent from the register | RR-12 | Could corrupt audit state if missing targets were accepted |
| C24 | attack | scope confusion | Try to scope a company-wide pricing policy to a customer | RR-8 | Could make a customer rule appear company-wide or vice versa |
