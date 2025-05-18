```markdown
# AI_AGENT.md

_Mission: autonomously fix or extend the codebase without violating the axioms._

---

## Runtime Setup

1. **Detect primary language** via lockfiles (`package.json`, `pyproject.toml`, …).
2. **Activate tool-chain versions** from version files (`.nvmrc`, `rust-toolchain.toml`, …).
3. **Install dependencies** with the ecosystem’s lockfile command (e.g. `npm ci`, `poetry install`, `cargo fetch`).

---

## CLI First

Use `bash`, `grep`, `curl`, `docker`, `kubectl`, `make` (and equivalents).  
Automate recurring checks as `scripts/*.sh`.

---

## Canonical Truth

**Code > Docs.** Update docs or open an issue when misaligned.

---

## Codebase Style & Architecture Compliance

- **Study before you code.**
  - Read key entrypoints, tests, and the last few merged PRs.
  - Identify prevailing design patterns, naming conventions, directory layout, lint rules, and CI checks.
- **Blend in, don’t reinvent.**
  - Match existing style and architecture unless a change is explicitly justified in the PR description.
  - Re-use helper functions and module boundaries instead of duplicating logic.
- **Propose, then alter.**
  - If a refactor is needed, open a small PR or issue explaining impact before large-scale changes.
- **New dependencies or frameworks require reviewer sign-off.**

---

## Axioms (A1–A10)

A1 **Correctness** proven by tests & types  
A2 **Readable in ≤ 60 s**  
A3 **Single source of truth & explicit deps**  
A4 **Fail fast & loud**  
A5 **Small, focused units**  
A6 **Pure core, impure edges**  
A7 **Deterministic builds**  
A8 **Continuous CI** (lint, test, scan)  
A9 **Humane defaults, safe overrides**  
A10 **Version-control everything**, including docs

---

## Workflow Loop

**PLAN → ACT → OBSERVE → REFLECT → COMMIT** (small & green).

---

## Autonomy & Guardrails

| Allowed                      | Guardrail                                |
| ---------------------------- | ---------------------------------------- |
| Branch, PR, design decisions | Never break axioms or style/architecture |
| Prototype spikes             | Mark & delete before merge               |
| File issues                  | Label severity                           |

---

## Verification Checklist

Run `./scripts/verify.sh` **or** at minimum:

1. **Tests**
2. **Lint / Format**
3. **Build**
4. **Doc-drift check**
5. **Style & architecture conformity** (lint configs, module layout, naming)

If any step fails: **stop & ask**.

---
```
