# Runtime isolation

`foundry_runtime` is an operator-invoked local adapter. It does not install a
scheduler or alter an active Hermes profile. The operator provides a disposable
native home, scratch directory, workspace, role credential, and immutable
binding when starting `Launcher.ensure`.

## Boundaries

- **Actor** — an actor is the identity in the immutable binding (for example,
  the assigned Worker or separate QA reviewer). `Client.authority` checks the
  current revision/digest, attempt, lease, assignment, and role before every
  exposed operation. A Worker can use only `foundry_action` operations for its
  assignment; it has no generic terminal, network, remote-Git, or integration
  capability. QA receives a separate credential and exact-candidate snapshot.
- **Sandbox** — supplied checks run through macOS `sandbox-exec`. The check
  backend denies network access and process forks, limits reads to approved
  system, workspace, and scratch roots, and limits writes to the workspace and
  scratch directory. If that verified backend is unavailable, the adapter
  rejects the check rather than falling back to an unsandboxed command.
- **Credential** — service and model credentials are operator inputs. The
  provider credential is passed privately over the launched process's stdin;
  it is not placed in the launch journal or model tool arguments. The child
  receives only the role credential needed for its bound service calls. GitHub
  credentials and transport remain operator-only.
- **AI.Contract** — AI.Contract is the authority for projects, immutable
  revisions, assignment and lease state, candidates, QA, and integration
  evidence. The local journal records launch identity and the shared remote
  gate; it is not a second work queue. QA acceptance retires the Worker but is
  not Done: only the Coordinator can reconcile target drift, deliver, verify,
  and record completion.

## Verify or recover safely

`Journal.inspect` (used by `Launcher.inspect`) returns `running`, `stopped`,
or `unknown` for a recorded launch. An `unknown` result is deliberately not
proof that the process did not start: for example, an intent may exist before
an acknowledged PID, or a PID may no longer identify the recorded process. Do
not start a replacement or signal an inferred process. Investigate the durable
launch identity first. `Launcher.stop(key)` only reports success after the
owned process group is confirmed stopped; otherwise recovery remains blocked.

For the local control suite, run:

```
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -m unittest discover -s tests -v
```

This verifies the repository's local controls; it does not establish a live
assignment, QA acceptance, integration, deployment, or remote GitHub access.
