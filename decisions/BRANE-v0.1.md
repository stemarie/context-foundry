# BRANE v0.1 — frozen Architect decision record

**Status:** confirmed by Karell; architecture only; implementation not authorized.

## Bound sources

- Master technical specification: https://docs.google.com/document/d/1IJpQaoZiWKtxCuaYcfzYCmt1LjouyQ5J1fmx5K9Ncu4/edit
- Document ID: `1IJpQaoZiWKtxCuaYcfzYCmt1LjouyQ5J1fmx5K9Ncu4`
- Target repository: https://github.com/stemarie/brane
- Baseline: `main` at `22300ca3cc8eb7726321c5d5e51a9b7fdd0a6289`

## Product decisions

1. **Core and delivery shape** — Rust only. BRANE begins as an in-process Rust library plus a small CLI/example harness. It is not a service, distributed system, or second-runtime hybrid.
2. **Logical clock** — callers use explicit host-driven control: submit input, advance a declared number of ticks, read outputs. No autonomous wall-clock loop exists in the core.
3. **Numeric contract** — all simulation values use signed Q32.32 fixed point. Supported CPUs must produce bit-identical snapshots and observable outputs from identical Blueprint, Snapshot, and ordered input/training streams.
4. **Arithmetic policy** — state and weight arithmetic uses explicit saturating Q32.32 operations; multiplication uses an `i128` intermediate and a documented round-half-to-even conversion to Q32.32. Invalid/out-of-range configuration is rejected rather than silently converted.
5. **Neuron model** — one discrete leaky integrate-and-fire model: deliver scheduled signals; for non-refractory neurons update activation with fixed decay; fire at/above threshold; reset activation; then apply configured refractory ticks.
6. **Anatomy** — v0.1 Regions contain homogeneous neuron populations. Directed Pathways use seeded fixed fan-out, uniform Q32.32 initial weights, and fixed integer delays. Cross-region edges outside declared Pathways are rejected.
7. **Training** — `local_expected_output_v1` is output-local supervised learning. It adjusts only plastic synapses that both entered a declared output population and participated within the configured eligibility window. Hidden-layer credit assignment is explicitly deferred.
8. **I/O** — inputs are direct Q32.32 values. Outputs are current activation values. Binary spikes and firing-rate encoders are deferred.
9. **Concurrency** — one deterministic serial reference engine and one deterministic Rayon parallel update engine ship together. Each tick uses a stable event ordering and stable merge; both engines must produce identical state/output.
10. **Persistence** — Blueprints are YAML. Snapshots and independently loadable Region artifacts are canonical CBOR with a SHA-256 integrity hash. Snapshots carry format, model and algorithm versions, numeric mode, seed, tick, realized graph/state, queued events, and training metadata.
11. **Seeded construction** — v0.1 uses a pinned `rand_chacha` ChaCha8 generator only while realizing Blueprint topology. The realized graph is persisted in a Snapshot; no runtime stochastic operation exists in v0.1.
12. **Proof scale** — tiny fixtures prove deterministic behavior; a shipped demo Blueprint contains 1,024 input neurons, 10,000 processing neurons, and 128 output neurons.

## Explicit non-goals

- No GPU, cluster execution, service/API server, scheduler, visual editor, LLM integration, rewiring, inhibitory neuron types, multiple neuron models, binary/firing-rate encoders, or hidden-layer credit rule.
- No BRANE source, tests, Git commits, pushes, releases, task cards, Worker, or Auditor execution is authorized by this record.

## Required evidence before implementation can be declared complete

- `cargo test --workspace` passes.
- The eight acceptance categories in the master specification each have a named deterministic test.
- Serial and parallel engines yield byte-identical Snapshots and output sequences.
- Save/resume output matches uninterrupted execution.
- The 1,024/10,000/128 demo loads, steps, trains through the output-local rule, snapshots, resumes, and reports an integrity hash.
