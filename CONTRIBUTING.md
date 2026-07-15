# Contributing

PRs welcome. Ground rules, which are also the product's values:

1. **No edge claims.** Strategies in this repo must be demonstrably naive and
   documented as such. PRs adding "profitable" strategies will be closed.
2. **No bundled venue data.** Fixtures must be synthetic and deterministic.
3. **Conservative by default.** Any new fill/fee/latency behavior defaults to
   the pessimistic setting; optimism must be opt-in and documented.
4. **Tests or it didn't happen.** `python -m pytest -q` must pass; new
   behavior needs new tests, including the failure path.
5. **Zero-dependency core.** New runtime dependencies go behind optional
   extras (like `[capture]`), never into the core.

Run checks locally:

```bash
pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
```
