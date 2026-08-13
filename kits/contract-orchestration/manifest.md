# Traceability manifest

| Artifact | Required concern | Failure prevented |
| --- | --- | --- |
| [Lifecycle README](README.md) | state vocabulary and complete cycle | false test, delivery, or deployment claims |
| [Coordinator/worker contract](AGENT.md) | current-source preflight and one writer | stale assumptions and concurrent checkout writers |
| [Recovery template](SOUL.template.md) | evidence-led reversible recovery | stale assumptions and unsafe path copying |
| [Coordination skill](skills/discrepancy-to-delivery.md) | deduplicated bounded contracts | duplicate contracts and lost continuation |
| [Implementation skill](skills/verified-implementation-delivery.md) | real checks and SHA equality | false test or delivery claims |
| [Card skill](skills/card-orchestration.md) | serialized durable orchestration | duplicate contracts and concurrent checkout writers |
| [Contract body template](templates/contract-template.md) | canonical editable `body_markdown` convention | competing contract-body shapes and implied runtime authority |
| [Contract-authoring skill](skills/contract-authoring.md) | portable authoring and consumption procedure | stale contract reads and inferred authority |
| [Generic templates](templates/README.md) | placeholders and receipts | unsafe secret/path copying and false delivery claims |
| [Adapter guidance](adapters/README.md) | honest capability mapping | lost continuation and a second control plane |
| [Validator guide](verification/README.md) | deterministic local checks | unsafe secret/path copying and false installed-event claims |
| [Validator](verification/validate.py) | files, sections, links, prohibited content | stale kit structure and unsafe copying |
