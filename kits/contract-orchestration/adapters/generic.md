# Generic adaptation path

1. Identify the authoritative work record, repository, default branch, and specification.
2. Map the Issue work-contract template and implementation-card template to the target tracker or durable file system.
3. Choose one existing continuation path: periodic audit or manual operator review.
4. Prove a bounded cycle: contract, one writer, real verification, authorized delivery, SHA comparison, and receipt.
5. Consider an optional completion accelerator only after the fallback loop is working and its safety contract is demonstrably enforceable.

Do not assume the target has events, cards, a scheduler, GitHub access, credentials, or push authority. The target adapter records its actual capabilities and leaves absent capabilities as manual steps.
