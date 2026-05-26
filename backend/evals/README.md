# Arohan Eval Framework

This framework now includes 8 evolved capabilities on top of endpoint pass/fail checks.

## 1) Scoring (quality, not only pass/fail)

- Every case can carry `weight` and `critical`.
- Run summary computes weighted `score_percent`.
- Critical failures force non-zero exit.

## 2) Baseline Comparison

- Save each run report (`backend/last_eval_report.json` by default).
- Compare with a previous run using `--baseline-report`.
- Shows `new_failures` and `fixed_failures`.

## 3) CI Automation

- Workflow file: `.github/workflows/ai-evals.yml`.
- Includes smoke eval on PR and optional full eval on manual dispatch.

## 4) Tiered Suites

Cases use `suite`: `smoke`, `core`, `full`.

- `--suite smoke`: fastest checks
- `--suite core`: smoke + core
- `--suite full`: smoke + core + full
- `--suite all`: everything exactly as tagged

## 5) Real Multimodal Asset Structure

- Asset catalog: `backend/evals/assets/catalog.json`.
- Keeps smoke assets and planned real injury assets tracked.

## 6) Safety Policy Checks

Per-case expectation supports:

- `must_contain_any`
- `must_not_contain`

This allows safety assertions like emergency escalation language.

## 7) Latency + Reliability Metrics

Run report includes:

- average and p95 endpoint latency
- per-case latency
- per-type pass rate and average latency

## 8) Future AGI Judge Loop

- `backend/evals/run_future_agi_judge.py`
- Exports eval dataset CSV and checks if `ai_evaluation` is installed.
- CSV output: `backend/future_agi_eval_dataset.csv`.

## Main Commands

Start backend:

```powershell
cd D:\intern\Arohan\backend
start_backend.bat
```

Run smoke suite:

```powershell
run_eval.bat --suite smoke
```

Run full suite + threshold:

```powershell
run_eval.bat --suite full --fail-threshold 75
```

Run with baseline diff:

```powershell
run_eval.bat --suite full --baseline-report D:\intern\Arohan\backend\last_eval_report.json
```

Prepare Future AGI dataset:

```powershell
venv\Scripts\python.exe evals\run_future_agi_judge.py
```
