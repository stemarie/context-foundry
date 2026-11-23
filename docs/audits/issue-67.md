# MCP-to-Architect planning acceptance

The disposable acceptance used the AI.Contract build from stemarie/AI.Contract#64
and a real Codex Architect. The fixture observed planning and held Worker
reservations idle to verify the authored Ready revision.

- An MCP client created a project and two milestones, authorized only the
  first milestone, and attached pinned specs. Requesting planning for the
  unapproved milestone failed at the application boundary.
- A request pointing at a missing Git commit was recorded as Blocked. The
  launch journal confirmed that no Architect ran for it.
- The client attached a Markdown snapshot of a synthetic external document.
  The registered runner consumed the project event, verified the attachment
  digest, and launched the Architect. The Architect used a requirement
  present only in the snapshot, authored a Ready revision bound to the same
  request and attachment, cited the source revision and section, and persisted
  its planning report. The runner recorded Completed after role exit.
- Replaying the MCP request and reconnecting a fresh Coordinator preserved the
  request ID and its single journaled Architect launch.
- The Git resolver test read the pinned committed bytes despite a different
  working-tree file. Snapshot tampering, absent Git sources and idle polling
  without a request were covered by focused tests.

The Python suite ran 146 tests with one skip. Skill packaging and diff checks
passed. The disposable acceptance used no production service or external
repository.
