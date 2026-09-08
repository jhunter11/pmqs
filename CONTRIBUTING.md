# Contributing

PMQS accepts changes to replay, accounting, capture, and research checks. Keep examples synthetic and reproducible. Example strategies should explain the mechanics without claiming an investment return.

New fill, fee, or latency options need a documented default and tests for failure cases. Explain which assumptions make a simulation optimistic or conservative. Keep runtime dependencies outside the standard library behind optional extras.

Before opening a pull request, run:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
```

Include the input fixture, expected behavior, and command results. Do not commit venue data, credentials, or personal records. A small deterministic fixture should reproduce the issue without network access.
