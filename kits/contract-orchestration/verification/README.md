# Local deterministic validation

Run from the repository root:

```sh
python3 kits/contract-orchestration/verification/validate.py --self-test
```

The command validates the checked-in kit and runs isolated negative cases in a temporary directory. It rejects missing required artifacts or sections, broken relative Markdown links, prohibited token/path patterns, and false installed-event-trigger claims. It uses only local repository content and removes its temporary directory before exit.

Run the plain check without negative cases with:

```sh
python3 kits/contract-orchestration/verification/validate.py
```
