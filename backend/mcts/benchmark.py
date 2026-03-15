# backend/mcts/benchmark.py
"""
MCTS Variant Analyser
=====================
Runs all 4 MCTS variants on the same query and returns a structured
analysis table with the following standard metrics:

Accuracy Formula — Task Success Rate (TSR):
  TSR (%) = (plan_score / 10.0) * 100

  This is the standard metric used in agentic task benchmarks
  (AgentBench, WebArena, ALFWorld). It measures how well the
  agent's plan achieves the goal on a normalised 0-100 scale.

Plan Quality Score (PQS) — the raw MCTS heuristic score (0-10).

Step Efficiency = plan_score / max(num_steps, 1)
  Reward per planning step — higher means more efficient.

Speed = wall-clock time in ms for the full MCTS run.

Improvement vs Baseline = ((tsr - baseline_tsr) / baseline_tsr) * 100
  % improvement over Basic-MCTS (the baseline variant).
"""

import time
from .variants import VARIANT_RUNNERS


def run_benchmark(query: str, simulations: int = 5) -> dict:
    """
    Run all 4 MCTS variants and return a full analysis table.

    Returns:
        {
          query, simulations,
          results: [ { variant, plan, num_steps, plan_score,
                       tsr_accuracy, step_efficiency, time_ms,
                       simulations, improvement_vs_baseline,
                       rank, description }, ... ],
          summary: { fastest, most_accurate, most_efficient,
                     best_overall, baseline_tsr }
        }
    """
    raw_results = []

    # ── Run all 4 variants ─────────────────────────────────────────
    for variant_key, runner in VARIANT_RUNNERS.items():
        try:
            result = runner(query, simulations)
            raw_results.append(result)
        except Exception as e:
            raw_results.append({
                "variant":     variant_key.upper(),
                "plan":        [],
                "score":       0.0,
                "simulations": simulations,
                "time_ms":     0.0,
                "error":       str(e),
                "description": f"Failed: {str(e)[:80]}",
            })

    # ── Compute standard metrics ───────────────────────────────────
    results = []
    for r in raw_results:
        plan       = r.get("plan", [])
        num_steps  = len(plan) if plan and plan != ["Direct Response"] else 0
        score      = r.get("score", 0.0)

        # Task Success Rate — standard agentic benchmark metric
        tsr = round((score / 10.0) * 100, 1)

        # Step Efficiency — reward per planning step
        step_eff = round(score / max(num_steps, 1), 2)

        results.append({
            "variant":           r.get("variant", variant_key),
            "plan":              plan,
            "num_steps":         num_steps,
            "plan_score":        round(score, 2),
            "tsr_accuracy":      tsr,           # primary accuracy metric
            "step_efficiency":   step_eff,
            "time_ms":           round(r.get("time_ms", 0.0), 1),
            "simulations":       r.get("simulations", simulations),
            "retrieved_snippets": r.get("retrieved_snippets", None),
            "description":       r.get("description", ""),
            "error":             r.get("error", None),
        })

    # ── Baseline (Basic-MCTS) metrics ─────────────────────────────
    baseline = next((r for r in results if r["variant"] == "Basic-MCTS"), None)
    baseline_tsr = baseline["tsr_accuracy"] if baseline else 0.0

    for r in results:
        if r["variant"] != "Basic-MCTS" and baseline_tsr > 0:
            r["improvement_vs_baseline"] = round(
                ((r["tsr_accuracy"] - baseline_tsr) / baseline_tsr) * 100, 1
            )
        else:
            r["improvement_vs_baseline"] = 0.0

    # ── Rank by TSR accuracy (desc), then speed (asc) ─────────────
    valid = [r for r in results if not r.get("error")]
    valid_sorted = sorted(valid, key=lambda r: (-r["tsr_accuracy"], r["time_ms"]))
    for i, r in enumerate(valid_sorted):
        r["rank"] = i + 1

    # Fill rank for errored variants
    for r in results:
        if "rank" not in r:
            r["rank"] = len(results)

    # ── Summary winners ───────────────────────────────────────────
    fastest        = min(valid, key=lambda r: r["time_ms"])        if valid else None
    most_accurate  = max(valid, key=lambda r: r["tsr_accuracy"])   if valid else None
    most_efficient = max(valid, key=lambda r: r["step_efficiency"]) if valid else None
    best_overall   = valid_sorted[0] if valid_sorted else None

    return {
        "query":       query,
        "simulations": simulations,
        "results":     results,
        "summary": {
            "fastest":          fastest["variant"]        if fastest        else "N/A",
            "most_accurate":    most_accurate["variant"]  if most_accurate  else "N/A",
            "most_efficient":   most_efficient["variant"] if most_efficient else "N/A",
            "best_overall":     best_overall["variant"]   if best_overall   else "N/A",
            "baseline_tsr":     baseline_tsr,
        },
        "metric_info": {
            "tsr_accuracy":    "Task Success Rate = (score/10)*100 — standard AgentBench/WebArena metric",
            "plan_score":      "Raw MCTS heuristic score (0–10)",
            "step_efficiency": "Score per planning step (reward/steps)",
            "time_ms":         "Wall-clock time for full MCTS run in milliseconds",
        },
    }