# Codex harness acceptance for issue 65

The disposable run used an AI.Contract executable with the project SSE endpoint,
a local bare Git remote, and Codex CLI 0.166.0. The Coordinator ran the same
watch, reservation, session supervision, and native completion paths as the
local operator command. The GitHub history adapter returned fixture references.

- A live Codex Architect enrolled three revisions and marked the dependent
  revision Ready first. Two live Codex Workers ran A and C concurrently.
- B stayed Ready through A's QA acceptance. Verified integration moved A to
  Done, and the Coordinator launched B without a manual reservation.
- The Workers committed through the assignment-bound MCP tool and submitted
  candidate evidence through AI.Contract. Separate live Codex QA sessions
  reviewed the exact candidates using auditor credentials. All three contracts
  reached Done and the bare remote contained all three expected files.
- The live run encountered an ownership observation race during cleanup.
  The supervisor now rechecks a process exiting between poll and inspection
  and keeps the journaled session leader identifiable during group shutdown.
- A second disposable run used the real service, local Git and scripted role
  subprocesses. A restarted Coordinator adopted both active Worker processes.
  Independent QA returned a correction for C, and the same attempt submitted
  a different candidate SHA before completion. The run completed and cleaned
  up successfully.

The Python suite ran 137 tests with one platform-specific skip. The role skills
passed packaging and reference checks. A real Codex session also completed an
authenticated native MCP project read. Production deployment and GitHub writes
from the disposable harness were outside this proof.
