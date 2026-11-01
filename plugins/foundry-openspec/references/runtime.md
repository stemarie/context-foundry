# Runtime and skill loading

This plugin supplies the Foundry and OpenSpec workflows across supported ChatGPT
and Codex surfaces. Load required sibling skills by their exact names through the
host's available skill-loading mechanism. Relative SKILL.md links are filesystem
fallbacks inside this package; do not require the author's personal skill folder.
If a required skill cannot be loaded, identify it and stop the affected workflow.

A ChatGPT project is not automatically a code checkout or a connected machine.
Resolve the user's target repository and execution host from the request and
available tools. Use existing connected GitHub and document tools for their
supported operations. Read and write project files or run CLI commands only when
the current chat actually provides that capability on the selected host. Never
claim that the plugin connects to bee2, Overmind or a shell by itself.

OpenSpec project workflows require OpenSpec CLI on the selected execution host.
Installed version used for these skills: 1.16.0. No machine paths, SSH keys or
account credentials are included. Setup and authentication remain separate.
When a required runtime/tool is unavailable, state the specific capability needed;
provide useful planning within authorized scope, but do not claim an OpenSpec
change was created, tests ran, or code was delivered without evidence.

Foundry Explore and Propose preserve their underlying exploration/planning scope.
Use foundry-start for explicitly requested execution; it owns cycle limits and
includes openspec-foundry for requirement mapping and verified task tracking.
Preserve the user's existing authorizations and the workflow's acceptance gates.


AI.Contract is the live execution authority. Use its project/milestone horizon, native revision/attempt/candidate bindings and supported actor/runtime adapters. OpenSpec remains planning and task tracking; GitHub issues are final historical records. Missing service/runtime capabilities are explicit blockers. Planning, skill installation and source delivery grant no deployment authority.

When invoked through a Foundry wrapper, that wrapper owns the final execution handoff to foundry-start. Official OpenSpec apply/verify/archive workflows remain available when directly requested; do not start a second executor inside a Foundry cycle.
