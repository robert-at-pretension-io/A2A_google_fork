```markdown
# CLAUDE.md

_A guide for any AI assistant collaborating on this codebase_

---

## 1 Project & Runtime Setup

1. **Detect the primary language(s).** Look for hallmarks such as `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `build.gradle`, etc.
2. **Activate the correct tool-chain version.**
   - Node → `.nvmrc`, `.tool-versions`
   - Python → `pyenv`, `.python-version`, `poetry.lock`
   - Rust → `rust-toolchain.toml`
   - Go → `go env GOTOOLDIR` version in `go.mod`
   - …other ecosystems as applicable.
3. **Install all dependencies using the project’s package-manager**, e.g.

   | Ecosystem | Typical command                                                     |
   | --------- | ------------------------------------------------------------------- |
   | Node.js   | `npm ci --ignore-scripts` &vert; `pnpm i --frozen-lockfile`         |
   | Python    | `pip install -r requirements.txt` &vert; `poetry install --no-root` |
   | Rust      | `cargo fetch`                                                       |
   | Go        | `go mod download`                                                   |
   | Java      | `./gradlew downloadAll`                                             |
   | Generic   | `./scripts/bootstrap.sh` (run if present)                           |

4. **Bootstrap sub-tools** (e.g., Git hooks, pre-commit, Husky) by executing any `./scripts/setup*` script at repo root.

---

## 2 Command-Line Investigation & Toolbox

> **Default to the CLI.** Rapid, scriptable diagnosis beats point-and-click.

| Task                 | Preferred tools (examples)                                    |
| -------------------- | ------------------------------------------------------------- |
| Search / slice files | `grep`, `ripgrep (rg)`, `awk`, `sed`, `jq`                    |
| Find files / dirs    | `fd`, `find`, `tree`, `ls -R`                                 |
| Shell scripting      | `bash`, `zsh`, POSIX sh (keep scripts portable)               |
| Process inspection   | `ps`, `top`, `htop`, `lsof`, `strace`                         |
| Networking           | `curl`, `httpie`, `dig`, `netstat`, `ss`                      |
| Containers           | `docker`, `docker compose`, `podman`                          |
| Orchestration        | `kubectl`, `helm`, `kind`, `k9s`                              |
| Build runners        | `make`, `just`, language-native CLIs                          |
| Log inspection       | `grep -i error`, `stern`, `kubectl logs -f`, `docker logs -f` |

**Guidelines**

1. **Replicate first.** Use `docker compose up` or `kind create cluster` to reproduce issues locally before coding.
2. **Automate inspection.** Prefer one-off shell scripts (`scripts/diagnose-*.sh`) to ad-hoc commands—commit them for reuse.
3. **Keep scripts portable.** Stick to POSIX utilities; gate GNU-specific features behind checks.
4. **Document useful snippets.** Add them to `/docs/cli-recipes.md` (create if absent).
5. **Fail fast.** Every CLI diagnostic script must exit non-zero on detectable failure.

---

## 3 Documentation & Source Alignment

> **Code is the ground truth.** Documentation is a guide that must accurately _reflect_ the codebase.

1. **Search for `.md` files** relevant to your task (`rg -i \.md`, `fd -e md`).
2. **Read docs before touching code** to understand intent, domain concepts, and accepted patterns.
3. **Verify docs ↔ code consistency.** If documentation contradicts implementation, treat implementation as canonical and:
   - Update the docs, **or**
   - Open an issue / PR proposing the required code change if the docs describe the _desired_ behaviour.
4. **Keep docs and code in sync**—no drift allowed.
5. **Run (or add) a doc-drift check** in CI; failing checks block merge.

---

## 4 Coding Principles (Immutable Axioms)

1. **Correctness First** – Code must meet spec & pass tests _before_ speed or style tweaks.
2. **Readable by Strangers** – Any competent engineer understands a function’s intent in ≤ 60 s.
3. **Single Source of Truth** – Represent each fact exactly once.
4. **Fail Fast, Loud, Early** – Detect invalid state at the source; raise explicit errors.
5. **Minimal Public Surface** – Export only what callers need today.
6. **Pure Before Impure** – Keep side effects at the edges.
7. **Small, Focused Units** – Functions < 50 LOC; classes < 200 LOC.
8. **Refactor Opportunistically** – Leave neighbouring code cleaner.
9. **Guard with Tests, Prove with Types** – Tests for behaviour; static types/contracts for invariants.
10. **Deterministic Builds** – Same inputs ⇒ bit-reproducible artefacts.
11. **Explicit Dependencies** – Declare every library, service, env-var.
12. **Version-Control Everything** – Code, config, schema, infra.
13. **Docs Adjacent, Verified** – Docs live beside code; CI checks for drift.
14. **Continuous Feedback Loop** – Every commit triggers lint, test, static-analysis, security scan; failures block merge.
15. **Humane Defaults, Safe Overrides** – Least-astonishment defaults; opt-in for risky behaviour.
16. **Follow Existing Standards** – The current codebase is canonical; mimic its style/configs and document new conventions when introduced.
17. **Verify Your Work** – Task is done only when proof exists (tests green, lints clean, artefact builds).

---

## 5 Iterative, Multi-Turn Workflow

1. **Work in cycles.** Typical loop: **Plan → Act (CLI/tool calls) → Observe → Reflect → Repeat**.
2. **Atomic steps.** Each cycle should accomplish a clear, verifiable chunk—don’t attempt the entire feature at once.
3. **Checkpoint often.** After each cycle, run tests and ensure doc/code alignment.
4. **Commit early & small.** Frequent, focussed commits simplify review and rollback.
5. **Use experiments wisely.** Spikes or throw-away prototypes are allowed but must be clearly marked and deleted or cleaned up before merge.

---

## 6 Autonomous Agency Guidelines

| Permission                       | Expectations                                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Branch & PR Creation**         | Create feature/fix branches without waiting; open PRs when changes build & test clean.                              |
| **Lightweight Design Decisions** | Choose libraries, minor patterns, or refactors that satisfy axioms; document rationale in PR description.           |
| **Experimental Prototyping**     | May build disposable spikes to validate ideas; spikes must be marked clearly and removed or converted before merge. |
| **Issue Filing**                 | Log bugs, tech-debt, or doc-drift you encounter; assign sensible severity labels.                                   |
| **Escalation**                   | If a decision could break public APIs or architectural boundaries, pause and request human review.                  |

_Use this autonomy to accelerate progress **without** waiving any axiom._

---

## 7 Proactive Axiom Enforcement

| Step                          | What you do                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------- |
| **Anticipate**                | Scan upcoming work for possible axiom clashes—including doc vs code mis-alignment. |
| **Autocorrect**               | Adjust design/code before reviewers must point it out.                             |
| **Suggest**                   | If a request conflicts with axioms, propose a compliant alternative.               |
| **Stay Consistent**           | Apply axioms to _all_ code you emit, even if not reminded.                         |
| **Improve Opportunistically** | When you spot legacy violations, file an issue or quick PR to fix.                 |

---

## 8 Verification Commands

Before opening a pull request:

1. **Run the project’s verification script** if present (`./scripts/verify.sh`).
2. Otherwise, at minimum execute:
   - **Tests** – `npm test`, `pytest`, `cargo test`, `go test ./...`, etc.
   - **Lint/Format** – `npm run lint`, `ruff check .`, `cargo fmt -- --check`, `golangci-lint run`, …
   - **Build** – `npm run build`, `cargo build --release`, `go build ./...`, `./gradlew build`, …
3. **Regenerate docs** for any public API changes (`npm run docs`, `cargo doc`, `mkdocs build`).
4. **Perform a doc-drift check**; ensure docs reflect the implementation.
5. **Confirm no axiom is violated**; if in doubt, stop and ask.

> **Axiom violations are fatal.** Investigate the codebase or ask clarifying questions—never guess.
```
