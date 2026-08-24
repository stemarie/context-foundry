# Foundry brief — BRANE v0.1

- **Objective:** Turn the approved BRANE technical specification into a bounded, frozen MVP implementation packet after Karell completes the required architecture decisions interview.
- **Reusable artifact:** `BRANE v0.1` Architect packet: a versioned implementation boundary, decision record, acceptance-test plan, and independently auditable Worker handoff. This intake itself does not authorize implementation.
- **Source of truth:**
  - Technical specification: `https://docs.google.com/document/d/1IJpQaoZiWKtxCuaYcfzYCmt1LjouyQ5J1fmx5K9Ncu4/edit`
  - Document ID: `1IJpQaoZiWKtxCuaYcfzYCmt1LjouyQ5J1fmx5K9Ncu4`
  - Target repository: `https://github.com/stemarie/brane`
  - Bound baseline: `main` / `22300ca3cc8eb7726321c5d5e51a9b7fdd0a6289`
- **In scope:** source/spec inspection; a one-question-at-a-time MVP decision interview; an Architect-owned decision record and implementation packet after Karell confirms it; deterministic acceptance-test design and an independent audit path.
- **Non-goals:** dispatching Foundry; creating Kanban cards; editing, committing, pushing, tagging, releasing, or otherwise changing `stemarie/brane`; starting a scheduler, monitor, gateway, API server, or external automation; credential changes; cluster/GPU implementation.
- **Role boundaries:** Architect owns interview, decision record, and bounded packet. Worker and Auditor are not activated by this intake. Any Worker code change requires a separate explicitly authorized packet; Auditor validates independently and does not remediate.
- **Acceptance criteria:**
  1. Context Foundry profile kit validates with named-profile Telegram disabled.
  2. The Doc ID, checkout origin, GitHub API target, branch, and baseline SHA are recorded and match.
  3. The MVP decisions needed to make the implementation deterministic are explicitly selected by Karell.
  4. The later implementation packet maps the specification's eight acceptance categories to deterministic checks.
  5. No BRANE code or external runtime state changes occur before a separate authorization.
- **Verification:** run `sync_foundry_profiles.py --check`; re-read this intake; verify target binding through Docs API, clean local checkout, and authenticated GitHub branch read-back; verify the Context Foundry board has no BRANE card or dispatched work.
