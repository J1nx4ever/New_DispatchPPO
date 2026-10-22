# PPO holdout evaluation

This protocol compares the completed PPO checkpoint with ALP policy 2
(grade-aware) on the same ten seeds that were not used in the 20-episode
training run. PPO actions are deterministic, and the evaluator never calls
`learn()` or updates weights.

## Held-out seeds

`ppo_holdout_seed_manifest.json` uses run indices 21-30 and experiment seeds
202610160031-202610160040. They do not overlap the training seeds
202610160011-202610160030.

## AnyLogic steps

Do not edit the `.alp` file through an automated script. In AnyLogic, open
`RL_Training` and make these changes manually:

1. Change `NumberOfRuns` from 20 to 10.
2. In the freeform parameter values, set:
   - `experimentRunIndex` to `(long) index + 21L` (was `(long) index + 1L`).
   - `experimentSeed` to `202610160031L + (long) index` (was
     `202610160011L + (long) index`).
3. For the baseline pass, set `currentDispatchPolicy` to 2 (grade-aware).
4. In the `finishEpisodeAndNotify` function, temporarily uncomment the existing
   `ruleEvalWrite(json.toString());` call (near the terminal JSON construction).
   It writes one record per run under `ore_waste_validation/`, named
   `policy2_run<run_index>_seed<seed>.jsonl`. Archive any conflicting files
   first; the logger deliberately refuses to create an already existing file.
5. Save and run `RL_Training` once for the baseline. No Python server is needed
   for policy 2.
6. Restore the `ruleEvalWrite` call to its original commented form, set
   `currentDispatchPolicy` back to 3, save, and confirm the model compiles.
   Restoring the function body is required because the Python ALP provenance
   check verifies its audited source hash.

These are temporary evaluation-only changes; policy choice and seed formulas
must be restored after the baseline pass. Keep the two conditions otherwise
identical.

## PPO pass

Start the inference-only evaluator:

```bash
conda run --no-capture-output -n anylogic-env \
  python -m python.evaluate \
  --model runs/ppo-20-episode-001/dispatch_ppo.zip \
  --episodes 10 \
  --anylogic-seed-manifest docs/ppo_holdout_seed_manifest.json \
  --output-dir runs/ppo-holdout-ppo-001
```

After `Dispatch gRPC listening` appears, start the saved `RL_Training`
experiment in AnyLogic for ten replications. The evaluator rejects seed/run
metadata that differ from the manifest. It records episode returns, terminal
reward metrics, action counts, and action-mask counts. It does not record
per-transition logs by default.

## Paired comparison

After PPO evaluation completes, compare paired seeds using the baseline JSONL
directory created by AnyLogic:

```bash
conda run --no-capture-output -n anylogic-env \
  python -m python.compare_heldout \
  --ppo-episodes runs/ppo-holdout-ppo-001/evaluation_episodes.jsonl \
  --baseline-dir ore_waste_validation \
  --output runs/ppo-holdout-comparison.json
```

The report contains per-seed and mean PPO-minus-baseline differences for ore
throughput, shift grade, and vehicle waiting time. Lower waiting time is
preferable; production and grade must be judged against the existing operating
targets. Ten paired seeds are an initial holdout check, not proof of
generalization or production readiness. The run manifest continues to mark
`alp_runtime_verified` false; GUI compilation, actual experiment settings, and
business behavior must be confirmed separately.
