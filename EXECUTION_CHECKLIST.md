# Execution Checklist — Predixion Final Round

Last updated: 2026-10-30 17:15 IST  
Current phase: **PRE-ASSIGNMENT SETUP COMPLETE**  
Assignment received: **NO**

Do not mark items done without verification.

Status tags: `[ ]` not started · `[~]` in progress · `[x]` done and verified · `[!]` blocked · `[N/A]` not required

---

## Live status

| Area | Status |
|---|---|
| Workspace inspected | [x] empty except context files |
| Toolchain inspected | [x] see context file |
| Docker daemon | [x] up tonight (`29.6.1`, Docker Desktop); re-check at 09:30 |
| Git isolation | [x] workspace-local `.git` (do not use `$HOME` repo) |
| Remote / GitHub repo | [ ] not created |
| Assignment parsed | [ ] waiting |
| P0 working | [ ] |
| Tests passing | [ ] |
| README accurate | [ ] |
| Decision log / walkthrough / founder prep | [ ] templates only |
| Submission artifact | [ ] |

---

## A. Assignment analysis (09:30–10:00)

- [ ] Read the full brief once without implementing
- [ ] Problem statement captured in context file
- [ ] Mandatory requirements listed (P0)
- [ ] Optional / stretch listed (P1/P2)
- [ ] Deliverables listed
- [ ] Tech constraints listed (language, cloud, libraries, forbidden tools)
- [ ] Evaluation criteria listed
- [ ] Submission channel and format listed
- [ ] Deadline confirmed (15:00 IST)
- [ ] Ambiguities recorded as assumptions
- [ ] Blocking questions asked (only if P0 is blocked)
- [ ] Smallest complete working slice defined

---

## B. Architecture (10:00–10:30)

- [ ] Target architecture in 10 lines or less
- [ ] Module / folder map
- [ ] Config via environment variables
- [ ] External dependencies named (and whether real vs mock)
- [ ] Failure modes that must be handled
- [ ] Security boundaries (secrets, auth, public vs private)
- [ ] Observability that the brief actually requires
- [ ] Cost / resource limits if cloud is in scope
- [ ] Trade-off recorded for the main architectural choice

---

## C. Core implementation (10:30–12:30)

- [ ] Repo initialized in this workspace only
- [ ] `.gitignore` covers env, venv, state, secrets
- [ ] `.env.example` created if config is required
- [ ] P0 happy path implemented
- [ ] App / infra runs locally (or `plan` succeeds if IaC-only)
- [ ] No hardcoded secrets
- [ ] Meaningful names, minimal dependencies
- [ ] First working checkpoint by 12:30

---

## D. Integration (12:45–13:45)

- [ ] Components wired end-to-end
- [ ] Real provider used if credentials exist; otherwise labeled mock
- [ ] Retries / timeouts / health only where relevant
- [ ] Invalid input rejected
- [ ] External service failure handled
- [ ] P1 items added only if P0 is stable

---

## E. Unit testing

- [ ] Test runner configured (pytest / npm test / go test / etc.)
- [ ] Core logic covered
- [ ] Invalid input cases
- [ ] Failure / timeout cases that exist in code
- [ ] Tests actually executed (paste command + result below)

```text
Command:
Result:
```

---

## F. Integration testing

- [ ] Main user / system workflow exercised
- [ ] API / CLI / pipeline responses checked
- [ ] Persistence checked if a DB is in scope
- [ ] Compose / local stack smoke test if containers are in scope
- [ ] Documented setup followed from a clean shell where practical

```text
Command / flow:
Result:
```

---

## G. Error handling

- [ ] Exceptions do not crash the process unchecked
- [ ] User-visible errors are explicit
- [ ] Partial failure behavior is defined
- [ ] Logs include enough context to debug (no secrets)

---

## H. Security

- [ ] `.env` not committed
- [ ] Secrets not in source, README, or screenshots
- [ ] Least-privilege IAM / tokens if cloud
- [ ] Input validation on trust boundaries
- [ ] Prompt-injection / unsafe tool use considered if LLM-scoped
- [ ] No public exposure of admin endpoints or state files

---

## I. Performance / reliability (only if relevant)

- [ ] Timeouts on outbound calls
- [ ] Bounded retries
- [ ] Resource limits (containers / Lambda / ECS / k8s)
- [ ] No accidental unbounded loops or unbounded payloads
- [ ] Cost-aware defaults (instance size, log retention, model choice)

---

## J. Documentation

- [ ] README: what it is, how to run, how to test
- [ ] Architecture section (short)
- [ ] Env vars documented
- [ ] Deploy + teardown if cloud
- [ ] Assumptions and known limitations
- [ ] Incomplete items listed honestly

---

## K. Final submission (14:30–15:00)

- [ ] Feature freeze (14:30)
- [ ] Full relevant test suite run once after freeze
- [ ] Decision log, walkthrough, founder prep match source (no invented details)
- [ ] 10-minute defense + 15–20 implementation-specific Q&A
- [ ] README matches actual commands
- [ ] `git status` / `git diff` inspected
- [ ] Meaningful commit(s)
- [ ] Remote created / pushed **only after user approval**
- [ ] Submission URL / zip / form completed
- [ ] Context file updated with final status

---

## Implementation ledger

| Item | Priority | State | Evidence |
|---|---|---|---|
| _fill after assignment_ | P0 | not implemented | |

States: implemented-and-verified | implemented-not-verified | partial | not-implemented | known-issue

---

## Command log (append, do not rewrite history)

- 2026-10-30: Environment inspected. Workspace empty. Docker was down, then started and verified. `gh` auth OK in normal shell. AWS default identity is root on `660442155240` / `ap-south-1`. Workspace git isolated from accidental `$HOME` repo.
