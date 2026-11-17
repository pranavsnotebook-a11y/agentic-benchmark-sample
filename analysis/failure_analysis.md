# Failure analysis: representative model attempt

Candidate: `analysis/naive_model_solution.py`. It's a typical one-shot pandas answer that
reads plausibly and runs without errors, but gets wrong numbers.

**pytest:** 4/11 passed. **Notebook:** 3/9 passed.

| # | Failed test | Root cause in candidate | Capability gap |
|---|-------------|-------------------------|----------------|
| F4 | exact 30-min gap continues | `gaps >= 30min` where the spec says *strictly greater* | Boundary semantics: the model paraphrases the rule instead of applying it literally |
| F2 | mixed offsets ordered by instant | `sort_values("ts")` on raw strings *before* parsing | Temporal reasoning: treats ISO strings as sortable, which only holds for a single offset |
| F5 | logout ends session | Session id built from gaps only | Multi-rule composition: the second boundary condition was dropped |
| F5 (+F2) | tie broken by event_id | `t2` (logout) and `t3` share an instant: the logout rule is missing, and no `event_id` tie-break is applied | Ignoring explicit tie-break + rule interaction at zero gap |
| F6 | plain int outputs | Returns `np.float64` from `total_seconds()` | Output-contract adherence |
| F1 | dedup independent of row order | `drop_duplicates(keep="last")`, which depends on file order, not `ingested_at` | Order of operations: ignores the field the rule names |
| all | background users | Combined effect of the above | n/a |

## Trajectory patterns worth flagging to the benchmark owner

1. **Premature success signal.** The code runs cleanly and returns well-shaped dicts, so an agent
   that only checks "does it execute" stops there. None of the bugs raise exceptions.
2. **Spec paraphrasing.** "More than 30 minutes" turns into `>=`, and "earliest ingested" turns into
   `keep=...`. The agent didn't re-read the spec after writing the code.
3. **Pipeline-order errors.** The agent sorted before parsing and deduplicated before validating.
   Each step looks fine on its own; only the sequence is wrong.
4. **Lucky passes.** With the shuffled main dataset, `keep="last"` passed the
   `u_dupes` test by chance. I added order-independent mini-CSV tests
   (`test_dedup_independent_of_row_order`, `test_naive_timestamp_is_invalid`) to make the
   check deterministic. Lesson for task design: every rule needs at least one test that
   cannot pass by row-order luck.

## Known limitation
`test_naive_timestamp_is_invalid` still passes for this candidate, because pandas coerces
mixed-format columns to NaT. A candidate using `pd.to_datetime(..., format="ISO8601")` would
treat naive values as UTC and fail it, so the test still discriminates in that case.
