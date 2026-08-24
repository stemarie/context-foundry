# BRANE v0.1 Implementation Packet

> **For Hermes:** This is an Architect packet, not dispatch authority. Do not create a Kanban card, invoke a Worker, edit `stemarie/brane`, or run an implementation command until Karell separately authorizes execution.

**Goal:** Implement a reproducible, deterministic Rust neural-runtime library that realizes the frozen BRANE v0.1 decision record.

**Architecture:** A pure `brane-core` crate owns fixed-point arithmetic, Blueprint validation/realization, sorted delayed events, serial and deterministic Rayon execution, output-local training, and canonical artifacts. A small CLI/example crate only loads a Blueprint, submits input, steps logical ticks, prints activation output, and proves snapshot/resume; it may not become a service.

**Tech stack:** stable Rust, `serde`, `serde_yaml`, canonical CBOR serializer, `sha2`, `rand_chacha` (pinned ChaCha8 construction only), `rayon`, `thiserror`, and `cargo test`.

---

## Immutable scope and source binding

- Specification: `1IJpQaoZiWKtxCuaYcfzYCmt1LjouyQ5J1fmx5K9Ncu4`
- Target: `stemarie/brane`, baseline `main@22300ca3cc8eb7726321c5d5e51a9b7fdd0a6289`
- Decisions: `decisions/BRANE-v0.1.md`
- Allowed future source paths: Rust workspace files, `examples/`, `tests/`, `README.md`, `docs/`.
- Forbidden: services, network listeners, cron, credentials, external integrations, cluster/GPU code, a second runtime, and changes outside the target repository.

## Required public core contract

```rust
let mut runtime = Runtime::from_blueprint(blueprint)?;
runtime.submit_input("input", values)?;
runtime.step(12)?;
let output = runtime.read_output("output")?;
runtime.train("input", input, "output", expected, training_ticks)?;
runtime.save_snapshot(path)?;
```

`step` is the only way the core logical clock advances. Every operation returns a typed error for unknown bindings, vector-length mismatch, invalid Blueprint, corrupt/incompatible artifact, and overflow/configuration violation.

## Implementation tasks

### Task 1: Establish the Rust workspace and baseline contract

**Files:** create `Cargo.toml`, `crates/brane-core/Cargo.toml`, `crates/brane-cli/Cargo.toml`, `crates/brane-core/src/lib.rs`, `README.md`.

1. Write compile-failing API-contract tests for `Runtime`, `Blueprint`, `Snapshot`, and `Q32_32` exports.
2. Add the smallest workspace that compiles the empty public API.
3. Run `cargo test --workspace`; record the initial pass.

### Task 2: Implement exact Q32.32 primitives

**Files:** create `crates/brane-core/src/fixed.rs`, `tests/fixed_point.rs`.

1. Write failing tests for parse/format, saturating addition/subtraction, `i128` multiply with round-half-to-even, comparison, and explicit out-of-range rejection.
2. Implement no-float Q32.32 arithmetic.
3. Run `cargo test --test fixed_point`.

### Task 3: Define and validate YAML Blueprints

**Files:** create `crates/brane-core/src/blueprint.rs`, `crates/brane-core/src/error.rs`, `tests/blueprint_validation.rs`, `examples/blueprints/three_region.yaml`.

1. Write failing tests for duplicate IDs, unknown Regions, zero/invalid fan-out, invalid delay, non-direct input, non-activation output, and invalid fixed-point fields.
2. Implement serde YAML parsing and validation.
3. Add the 1,024/10,000/128 demo Blueprint and a tiny test Blueprint.
4. Run `cargo test --test blueprint_validation`.

### Task 4: Realize deterministic anatomy

**Files:** create `crates/brane-core/src/ids.rs`, `crates/brane-core/src/graph.rs`, `tests/deterministic_construction.rs`.

1. Write the failing test that the same Blueprint/seed creates byte-identical stable IDs and sorted synapse lists.
2. Pin ChaCha8 construction and create homogeneous Region populations plus fixed-fan-out Pathways.
3. Reject any undeclared cross-region edge.
4. Run `cargo test --test deterministic_construction`.

### Task 5: Build ordered delayed-event scheduling

**Files:** create `crates/brane-core/src/event_queue.rs`, `tests/wave_ordering.rs`, `tests/strict_pathways.rs`, `tests/recurrence.rs`.

1. Write failures proving events cannot arrive before `emission_tick + delay`, undeclared pathways cannot deliver, and a recurrent loop advances across ticks rather than recursively.
2. Implement a canonical ordering key `(delivery_tick, target_region, target_neuron, source_region, source_neuron, synapse_id)`.
3. Run the three focused test targets.

### Task 6: Implement the serial LIF reference runtime

**Files:** create `crates/brane-core/src/lif.rs`, `crates/brane-core/src/runtime.rs`, `tests/deterministic_execution.rs`, `tests/io_contract.rs`.

1. Write failures for delivery → state update → threshold → reset/refractory behavior and direct input/activation output bindings.
2. Implement explicit `submit_input`, `step`, and `read_output` behavior.
3. Run `cargo test --test deterministic_execution --test io_contract`.

### Task 7: Add deterministic Rayon execution

**Files:** modify `runtime.rs`; create `crates/brane-core/src/parallel.rs`, `tests/serial_parallel_equivalence.rs`.

1. Write failures requiring serial and parallel paths to yield identical output sequences, queued events, and Snapshot bytes.
2. Partition eligible neuron updates; collect generated events locally; sort/merge canonically before the next tick.
3. Run `cargo test --test serial_parallel_equivalence`.

### Task 8: Implement output-local supervised training

**Files:** create `crates/brane-core/src/training.rs`, `tests/training_locality.rs`.

1. Write failures proving only recently used, plastic synapses entering output populations change, and frozen/training-disabled modes do not alter weights.
2. Implement eligibility traces, expected-vs-actual activation error, bounded/saturating updates, and version tag `local_expected_output_v1`.
3. Run `cargo test --test training_locality`.

### Task 9: Implement canonical persistence and Region artifacts

**Files:** create `crates/brane-core/src/artifact.rs`, `tests/save_resume.rs`, `tests/region_portability.rs`, `tests/artifact_integrity.rs`.

1. Write failures for Blueprint/YAML round-trip, canonical CBOR Snapshot bytes, SHA-256 mismatch refusal, continued-output equality after reload, and independent Region interface preservation.
2. Persist format/model/algorithm/numeric versions, seed, tick, realized state, queue, and training metadata.
3. Run the three focused test targets.

### Task 10: Ship the bounded CLI/example and full verification

**Files:** implement `crates/brane-cli/src/main.rs`, `examples/three_region.rs`, `tests/demo_scale.rs`, `README.md`.

1. Write a test proving the documented demo Blueprint constructs, accepts input, steps, trains, snapshots, resumes, and emits an integrity hash.
2. Implement a local-only CLI that demonstrates the library; no listener or long-running runtime.
3. Run `cargo fmt --check`, `cargo clippy --workspace -- -D warnings`, and `cargo test --workspace`.

## Acceptance mapping

| Master-spec category | Required test |
|---|---|
| Deterministic construction | `deterministic_construction` |
| Deterministic execution | `deterministic_execution` and `serial_parallel_equivalence` |
| Strict pathways | `strict_pathways` |
| Wave ordering | `wave_ordering` |
| Recurrence | `recurrence` |
| Training locality | `training_locality` |
| Save/resume | `save_resume` |
| Region portability | `region_portability` |

## Worker evidence and independent audit requirements

A later Worker must provide exact commands, versions, test output, changed-path list, baseline/final SHA, and proof that no forbidden runtime behavior was introduced. A later independent Auditor must re-run the acceptance suite from a clean checkout, compare serial/parallel Snapshot bytes, verify the Source binding, and reject any service, scheduler, external integration, or scope expansion.
