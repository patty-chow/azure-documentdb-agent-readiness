---
title: "Note only: application heuristics (scoring formulas, thresholds, retry counts, TTLs, schedulers, external APIs, app surface) are builder decisions, not Learn or agent-kit gaps"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 12
findings: 14
bucket: learn-information_gap
verdicts:
  skipped: note-only
---

# Note only: application heuristics are builder decisions, not doc gaps

In 14 readiness-stage information_gap findings across 12 samples, gpt-5-mini asked Learn (or the agent kit) to prescribe business logic that exists only in the invented sample scenario: sanctions match-confidence weights, an affinity-score formula, insider-threat and ATM thresholds, a journal dedupe policy, cache TTL / stale-while-revalidate windows, webhook payload and retry policy, optimistic-locking retry counts, refresh cadence and scheduler choice, NCBI E-utilities rate limits, web-search provider choice, and CLI vs HTTP API surface. None is a property of Azure DocumentDB.

Learn already documents the primitives these decisions rest on (cosmosSearch searchScore, TTL indexes via expireAfterSeconds, multi-document transactions, retrywrites=false), and the agent kit's connection skill shows a generic exponential-backoff pattern. The builders picked sensible, configurable defaults and recorded them in 04-decisions.md and README (for example sanctions D008, open-banking D008, shopping-cart D005), and the audit stage did not escalate them.

Possible follow-up, outside this theme: the experiment harness could tag information_gaps about formulas, thresholds, cadences, external APIs or app surface as "builder-decision" so they are not counted against Learn.

## Verification

- skipped: note-only. The three checks were not run. Skip reason: every finding asks for scenario-specific application constants, not service facts; the primitives are documented and the builders resolved each one correctly. The skip reason is strong, so status is drop.

## Finding ids

F0467, F0470, F0833, F2660, F2756, F2887, F2917, F2953, F3122, F3189, F3238, F3270, F3403, F3438
