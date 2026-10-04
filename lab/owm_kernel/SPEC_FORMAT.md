# Decision specs as data: the format

A **decision spec** is a YAML file that describes one kind of governed decision. A generic runner
(`flow.py`) executes it over a corpus of documents and system-of-record tables. A spec contains no
code: every value is an **expression** in a small, safe language (below), and expressions can call
the governed functions listed here. This file is all a spec author needs.

## The shape of a spec

```yaml
spec: my_decision                  # a name
outcomes: [A, B, C]                # the outcome vocabulary; the decision is exactly one of these
route_to: C                        # the outcome a person should see when the engine is unsure

documents:                         # which documents count, and who may issue them
  kinds:                           # first matching rule wins, by doc_id prefix, title words or owner
    - { kind: policy, id_prefixes: [POLICY-], title_words: [Policy] }
    - { kind: letter, title_words: [Letter] }
  owners: { policy: [Operations], letter: [Legal] }   # the only owners whose documents qualify
  policy_kind: policy              # the kind whose versions (validity windows) govern on a date
  graded: [letter]                 # other kinds that must pass the provenance check to be used

helpers:                           # named one-argument functions; the argument is `x`
  pct: 'int(x.rstrip("%")) / 100'

readers:                           # named functions over a document; the argument is `doc`
  amount: 'maybe(money, search(r"up to \$([\d,]+)", doc.body))'

questions:                         # questions for the judgment engine (see judge)
  same_party:
    type: choice                   # choice: pick one criterion; noul: a probability a statement is true
    instructions: Is the company in `a` the same legal entity as the one in `b`?
    criteria: { same: "Yes", different: "No", unclear: Cannot tell }

steps:                             # computed in order; each is `name: expression`
  - row: 'first(r for r in table("orders") if r["order_id"] == record["order_id"])'
  - pol: 'in_force(policies(), as_of)'
  - big: { when: 'pol is not None', expr: 'float(row["value"]) > 1000' }   # skipped → None

outcome:                           # an ordered decision table; the first rule that holds decides
  - { when: 'pol is None', outcome: C }
  - { when: 'big', outcome: B }
  - { outcome: A }

then:                              # optional steps that need `outcome`
  - who: '[...] if outcome == "B" else []'

obligations:                       # optional: duties the decision creates, each with a condition
  - { when: 'big', party: organization, duty: notify, role: '"MANAGER"',
      holder: 'holder_of("Operations Manager")', due: 'as_of + days(2)' }

record:                            # the decision record: field → expression
  scenario: sid
  outcome: outcome
  gated_outcome: gated_outcome
  uncertain: uncertain
  judgments: judgments
  flags: flags
```

**How it runs:**
1. The provenance check (from `documents`). Documents of a listed kind count only if their owner is
   listed for that kind and they aren't marked as a draft, a proposal, pending or unexecuted.
2. The `steps`, in order.
3. The `outcome` table, then the `then` steps, then the `obligations`.
4. **Gating:** if any judgment you recorded with `use` was uncertain, or a document you marked with
   `rely` shows tamper signs, `gated_outcome` becomes `route_to`.
5. The `record`.

**Inputs** (the names available from the start) depend on the decision. The task you were given
says what they are. Always available: `sid`, the scenario id.

Steps whose name starts with `_` are for side effects only (`use`, `rely`, `flag`). In a YAML
single-quoted string a backslash is literal, so regular expressions read naturally. Write Python
strings inside the expression with double quotes. Long expressions can use a YAML block scalar
(`>-`).

## The expression language

A safe subset of Python expression syntax. It is interpreted, never executed as code.

| Allowed | Examples |
|---|---|
| literals, arithmetic, comparisons, `and` / `or` / `not`, `x if c else y` | `a + b * 2`, `0 < x <= 10`, `"y" if ok else "n"` |
| subscripts and slices | `row["name"]`, `s[:7]`, `pair[0]` |
| dict, list, tuple and set literals; comprehensions; generator expressions (lazy) | `{k: v for k, v in pairs}`, `[r for r in rows if r["x"]]`, `next((d for d in ds if ok(d)), None)` |
| f-strings | `f"no claim by {deadline}"`, `f"{amount:.2f}"` |
| calls to the functions below, and these methods | strings: `startswith endswith split rsplit strip lstrip rstrip lower upper replace partition join splitlines isdigit format`; dicts: `get keys values items`; dates: `date isoformat strftime astimezone`; calendars and clocks: see below |
| these attributes | `doc.body doc.doc_id doc.title doc.owner doc.front doc.filename`; `timedelta.days`; `date.year .month .day`; `calendar.opens .closes .zone` |

**Not allowed:** imports, lambdas, assignment (use steps), other attributes or methods, and anything
starting with `_`.

## Functions

### Pure helpers

| Function | What it does |
|---|---|
| `min max sum len round abs any all sorted float int str bool set list dict tuple zip next iter` | as in Python |
| `first(items)` | the first item, or `None` |
| `latest(items, field)` | the item with the greatest `item[field]` (a `(start, end)` window counts by its start), or `None` |
| `unique_by(items, field)` | keeps the first item for each value of `item[field]` |
| `union(list_of_sets)` | their union |
| `intervals(starts, ends)` | pairs each start time with the first end after it: `[(start, end), …]` |
| `date("2026-01-31")`, `datetime("2026-01-31T09:00:00-05:00")` | parse ISO dates and times |
| `days(n)`, `minutes(n)` | durations, for date arithmetic (`(d2 - d1).days`) |
| `combine(date, clock_time)`, `clock_time(h, m)`, `zone("America/Chicago")`, `max_date` | build times |
| `search(pattern, text, group=1)` | the regex group, or `None` (`.` matches newlines) |
| `groups(pattern, text)` | all the groups as a tuple, or `None` |
| `findall(pattern, text)` | all matches (multi-line: `^` matches each line, `.` matches newlines) |
| `paragraph(text, needle)` | the first blank-line-separated paragraph containing `needle`, flattened, or `None` |
| `paragraphs(text)` | all the paragraphs |
| `flat(text)` | whitespace collapsed to single spaces |
| `money("$1,250,000")` | `1250000.0` |
| `maybe(f, x)` | `f(x)`, or `None` if `x` is `None` |
| `row(doc, "Field")` | the value of a `| Field | value |` row in a document's table, as `"Field: value"`, or `None` |
| `window(doc)` | the document's validity `(start, end)` from front matter `effective_from` / `effective_to` (an open end is `max_date`), or `None` |
| `products_in(text, products)` | the product SKUs that `text` names, by SKU or full name |
| `referenced_agreement(doc)` | the id after "Agreement:" or "agreement", if any |

### Evidence

| Function | What it does |
|---|---|
| `table(name)` | the rows (dicts of strings) of the system-of-record export `structured/<name>.csv` |
| `staff`, `products` | the HR roster and the item master, as rows |
| `docs(kind)` | the documents of a graded kind that passed the provenance check |
| `policies()` | the documents of `policy_kind` that passed it |
| `covering(docs, on)` | those whose validity window contains the date `on` |
| `in_force(docs, on)` | the single one in force on `on`; `None` when none is, or when two or more are (recorded as a conflict) |
| `linked(row, rows, keys)` | the row in `rows` that shares every key in `keys` with `row` (identity by a registered identifier, such as a DUNS number), or `None` |

### Judgment

The judgment engine answers narrow questions about text, with calibrated probabilities. Use it for
soft judgments: is this the same company, does this text say X. Don't use it for numbers, dates or
rules; those are expressions.

| Function | What it does |
|---|---|
| `judge(name, state)` | asks the question `questions[name]` about `state` (a dict whose keys the question's instructions name in backticks). It returns `{"choice", "probabilities", "confidence", "uncertain"}` for a choice question, or `{"noul", "yes", "uncertain"}` for a noul question. |
| `ask(name, question, state)` | the same, with a question built in an expression (for example, criteria read from a document) |
| `use(j, …)` | records judgments (for gating and the record) and returns the last one. **Only recorded judgments can route a decision to a person.** |
| `uses(list)` | records a list of judgments |

### Authority and people

| Function | What it does |
|---|---|
| `authority(policies, on, amount, requested_by)` | Reads the approval bands of the single policy in force on `on`, from the bullet sentences under the policy's `## 3. Approval authority` heading. It accepts these sentences: "- <Role plural> may approve <things> up to and including <amount>" and "- <Things> greater than <amount> [and up to and including <amount>] require <Role> approval", with amounts as `N%` or `$N`. It maps each role to an HR job title (a judgment), finds the requestor in HR by email (`requested_by`), and finds the approver: the first holder of the required title up the requestor's manager chain, else any holder. Under a policy that says no one "may approve or concur on" a request "they submitted", the requestor is never authorized, and a requestor who would be their own approver passes it to their manager. It returns `{"policy", "requestor_limit", "requestor_authorized", "required_role", "approver", "_doc"}`, or `None` when no single policy is in force. `_doc` is the policy document. |
| `concurrences(policy_doc, amount, tier, requested_by)` | Reads the policy's "- For <Tier> accounts, <things> greater than <amount> also require <Role> concurrence" sentences, and returns the HR rows of the people who must concur for this amount and account tier, resolved like the approver. |
| `holder_of(role_words)` | the employee id of the single holder of the HR title the words refer to (a judgment), or `None` |
| `owner_of(row)` | the HR row of the person whose email is the row's `owner_email` |
| `map_role(role_words)` | the HR job title the words refer to (a judgment) |

### Clocks

| Function | What it does |
|---|---|
| `calendar(zone, opens, closes, holidays)` | business hours in a time zone, minus a list of holiday dates. Methods: `local(t)`, `next_open(t)`, `add(t, minutes)`, `working_day(d)`, `working_days_after(d, n)`, `working_days_between(a, b)`. Attributes: `opens`, `closes`, `zone`. |
| `clock(calendar, business, start, excluded)` | a clock from `start`, counting all time (`business` false) or business hours only, minus the excluded `(start, end)` intervals. Methods: `elapsed(t)` (in minutes), `moment(minutes)` (when it reaches them). |

### Effects

| Function | What it does |
|---|---|
| `rely(doc, …)` | marks documents the decision relies on (for tamper checks); lists are accepted |
| `flag(text)` | adds a note to the record's `flags` |

## Available after the outcome

Use these in `then`, `obligations` and `record`: `outcome`. Use these in `record`:
`gated_outcome`, `uncertain`, `judgments`, `flags`, `obligations`.
