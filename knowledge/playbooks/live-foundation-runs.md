# Playbook: runs against a live foundation (Utopia, B-20, or any knowledge base)

**Use it for** any reader run, ingestion, correction, curation or rebuild on a live knowledge
foundation. It comes from the first live runs (R1), the luna baselines and the bench (R4), and the
exam (R5); see [patterns.md](../patterns.md).

## Before touching it

- [ ] **Verify the foundation's model, effort and settings at the source,** never from a note. Record
      why each setting was chosen, and what would retire it.
      ([The workaround baseline](../patterns.md#the-workaround-baseline),
      [Second-hand facts](../patterns.md#second-hand-facts))
- [ ] **Price the foundation's side, not only the reader's.** Ingestion and governance spend scale
      with the corpus and the queue. Check the provider's spend limit, and tell the user before any
      rebuild. The user has cited "$75" and "over $80" for past rebuilds.
- [ ] **Fingerprint what runs:** the binary's sha256, each workspace's model and effort, document
      and fact counts. Compare them with the baseline's. ([Instrument drift](../patterns.md#instrument-drift))
- [ ] **New conditions get their own workspace or base.** Never test in the instrument of record.
- [ ] **Snapshot before changing anything,** or clone a base per condition. List the irreversible
      steps, and get the user's OK. ([Undo isn't never-happened](../patterns.md#undo-isnt-never-happened))
- [ ] **Rehearse on a fresh instance, through the same load path,** with every guard.
      ([The rehearsal isn't the performance](../patterns.md#the-rehearsal-isnt-the-performance))

## Loading and settling

- [ ] Pin the corpus by file hashes, and check every corpus before the first upload.
- [ ] **"Settled" means** no queued or failed job in any background process, and no provider errors
      in the server log. If the log can't be read, say so.
      ([Settled by the wrong signal](../patterns.md#settled-by-the-wrong-signal))
- [ ] Known defects' workarounds run in provisioning (for example, `today.py load` writes version 1
      rows).

## Reading it

- [ ] **Probe each reader variant:** the tools it sees, the MCP server connected, no denials. Hide
      tools with `--disallowedTools`.
- [ ] **Probe the agent's ambient context:** who it works for, and today's date. Run it under an
      empty config with its own token. ([Ambient context](../patterns.md#ambient-context))
- [ ] Use a read token per run, scoped to the run's bases, and revoke it at the end.

## Changing it, and after

- [ ] After any withdrawal, revert or delete, search the reader's tool results for the old values,
      and add a control that hides residual paths.
- [ ] After a data fix under a running service, check the service's answer, not only the data.
      ([Cached absence](../patterns.md#cached-absence))
- [ ] Record which instance holds which dataset version. Name any instance change in the run's name.
- [ ] **Teardown:**
  - revoke tokens and users;
  - archive without the key- and token-bearing tables, and check for key prefixes;
  - stop the servers, drop the databases, and delete the local secret files.
