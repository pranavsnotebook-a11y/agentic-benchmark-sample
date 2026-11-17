# Agentic Benchmark Sample: Clickstream Sessionization

A self-contained benchmark task built to expose **logical-reasoning failures** in AI coding
agents. The task looks like routine data engineering, but each rule hides a trap that
plausible-looking code gets wrong.

```
task/instruction.md        problem statement given to the agent
task/make_data.py          deterministic dataset generator (edge cases + seeded traffic)
task/data/events.csv       generated dataset (255 rows, shuffled)
task/metadata.json         task metadata and targeted reasoning skills
solution/solution.py       golden solution (stdlib only)
tests/test_sessionize.py   pytest suite (11 tests)
tests/unit_tests.ipynb     notebook version of the checks
analysis/                  a representative flawed model attempt + failure analysis
```

## Run

```bash
uv venv && uv pip install pandas pytest nbformat nbclient ipykernel
python task/make_data.py
pytest -q tests                                              # golden: 11 passed
SOLUTION=analysis/naive_model_solution.py pytest -q tests     # flawed: 7 failed
```

## Traps the task targets
- An exact 30:00 gap must **not** split a session (strict `>`)
- Mixed UTC offsets, where text order differs from time order
- `logout` forces a boundary even after a short gap
- Duplicate rows that conflict, resolved by earliest `ingested_at` rather than file order
- Invalid or naive timestamps dropped *before* deduplication
- Deterministic tie-breaking on identical instants
- Output must be plain `int`s

See `analysis/failure_analysis.md` for the per-test root-cause breakdown.
