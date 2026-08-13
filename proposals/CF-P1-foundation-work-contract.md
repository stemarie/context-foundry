# CF-P1 Foundation Work Contract

**Issue:** assigned at creation time  
**Owner:** `foundry-worker` (under Architect routing)  
**Repository:** `stemarie/context-foundry` (`main`)  
**Kanban board:** `context-foundry`

## Objective

Build the Context Foundry Phase 1 foundation required to execute one *subsequent*, approved, read-only pilot packet. This contract does not authorize the pilot Worker investigation itself before Karell approves the Architect-selected corpus.

## In scope

- An informative `README.md` defining Phase 1 scope, roles, safety boundaries, workflow, checks, and terminal rule.
- Versioned project and source policies in `config/`.
- JSON schemas for source manifests and evidence artifacts.
- Deterministic standard-library scripts to inventory explicitly named files, extract bounded UTF-8 text, and validate evidence against a packet.
- Role-local skills for Architect, Worker, and Auditor, plus bounded packet/template contracts.
- A starter Phase 1 state file and an empty source manifest.
- Tests proving that the validator accepts a cited fact and rejects an uncited fact.

## Out of scope

- Executing the pilot question or selecting the final corpus.
- Any corpus reads beyond named smoke-test files.
- Phase 2+ monitors, health jobs, retrospectives, free-form recursion, or autonomous external action.
- Public, destructive, financial, legal, credential, or unrelated system changes.

## Acceptance criteria

1. `python3 -m py_compile scripts/*.py` succeeds.
2. `python3 -m unittest discover -s tests -v` succeeds.
3. `python3 scripts/inventory.py --manifest /tmp/context-foundry-manifest.json --source README.md --source config/foundry.yaml` succeeds.
4. `python3 scripts/extract.py --manifest /tmp/context-foundry-manifest.json --source-id src-001 --output /tmp/context-foundry-readme.extract --max-chars 200` creates exactly 200 characters.
5. `git diff --check` succeeds.
6. The verified commit is pushed to `main`, linked to and closes the GitHub Issue, and its local SHA equals `refs/heads/main` on GitHub.

## Evidence receipt

Record exact command outcomes, resulting commit SHA, remote branch SHA, GitHub Issue URL/state, and the artifact path for this contract. Do not include credentials.
