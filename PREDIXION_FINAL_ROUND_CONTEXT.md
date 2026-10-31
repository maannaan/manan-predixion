# Predixion Final Round — Persistent Engineering Context

Last updated: 2026-10-30 17:15 IST  
Status: Environment prepared. Assignment not yet received. Do not invent requirements.

---

## 1. Candidate and evaluation

- Candidate: Manan Paliwal
- Role: Forward Deployment Engineer, Predixion AI
- Stage: Final technical evaluation
- Assignment window: 09:30–15:00 IST (5.5 hours)
- Founder discussion: 15:15–16:00 IST
- GitHub: `maannaan`
- Git identity (global, do not modify): `Manan <croodycoder@gmail.com>`

Default schedule:

| Time | Focus |
|---|---|
| 09:30–10:00 | Requirements, P0/P1/P2, assumptions |
| 10:00–10:30 | Architecture + project skeleton |
| 10:30–12:30 | Core implementation |
| 12:30–12:45 | First working checkpoint |
| 12:45–13:45 | Secondary features + integration |
| 13:45–14:30 | Tests, debugging, critical fixes |
| 14:30–14:50 | README, env template, verification |
| 14:50–15:00 | Commit, push, submit |
| 14:30 | Stop nonessential features |
| 14:50 | Submission-only mode |

---

## 2. Technical background (use this, do not re-explain basics)

DevOps / cloud platform engineer, 2+ years.

Strengths: AWS/Azure/GCP/on-prem, Terraform, CloudFormation, Ansible, Docker, Kubernetes, Helm, CI/CD (GitHub Actions, Jenkins, GitLab, CodePipeline, Azure DevOps), observability (Prometheus, Grafana, Datadog, OTel, CloudWatch, ELK/OpenSearch), Python/FastAPI/Go/Java, LangChain/LangGraph/CrewAI/MCP, RAG, WhisperX/vLLM/Ollama.

Recent work: multi-cloud infra, CI/CD across 25+ workflows, CFN→Terraform, GPU WhisperX, agentic platform engineering.

---

## 3. Predixion domain (context only — not assignment requirements)

- Products: VOIZ, KOLLECT
- Domain: agentic AI, voice automation, BFSI / digital lending, collections, Indian-language voice agents, production AI infra
- Prior round involved STT→LLM→TTS, retries/backoff, circuit breakers, DLQ, failure injection, model-independent inference, ECS Fargate, Terraform, custom-metric autoscaling, CloudWatch, cost, deploy/teardown
- **Do not assume the new assignment matches the previous round**

---

## 4. Machine and workspace

- Host: macOS 26.6.2 (Darwin 25.6.0), x86_64
- CPU: Intel Core i7-1068NG7 @ 2.30GHz, 8 cores
- RAM: 32 GB
- Disk: ~98 GB free
- Shell: zsh
- Workspace: `/Users/apple/Desktop/Steadfast-part 2`
- Workspace was empty at setup. No assignment code yet.

**Git trap:** `/Users/apple` is an accidental empty git repo (no remotes, no commits of value). Never run git commands from `$HOME`. Always `cd` into this workspace first. This workspace has its own `.git`.

---

## 5. Installed tool versions (verified 2026-10-30)

| Tool | Version / path | Notes |
|---|---|---|
| `python3` (default) | 3.9.6 `/usr/bin/python3` | **Do not use.** Xcode system Python. |
| Python 3.11 | 3.11.16 `/usr/local/bin/python3.11` | OK fallback |
| Python 3.12 | 3.12.13 `/usr/local/bin/python3.12` and uv | **Preferred default** |
| Python 3.13 | 3.13.18 | OK |
| Python 3.14 | 3.14.8 | Avoid unless required |
| uv | 0.11.3 | Preferred for venv + deps |
| pip (3.12) | 26.0.1 | |
| Node.js | v22.14.0 | via `~/.rote/bin/node` |
| npm | 10.9.2 | |
| Git | 2.50.1 (Apple Git-155) | |
| Docker | 29.6.1 | Docker.app installed |
| Docker Compose | v5.3.0 | plugin + `docker-compose` binary |
| Terraform | v1.17.0 | latest is 1.17.1; fine |
| Go | 1.27.1 | |
| Java | OpenJDK 21.0.8 (Android Studio JBR) | |
| AWS CLI | 2.36.24 | |
| GitHub CLI | 2.97.0 | auth OK as `maannaan` |
| kubectl | v1.36.1 | no current context |
| Make | GNU Make 3.81 | |
| curl | 8.7.1 | |
| jq | 1.7.1 | |
| Homebrew | 7.0.10 | Intel `/usr/local` |
| gcc/clang | present (Xcode CLT) | |
| Redis CLI | 8.6.2 | |
| MySQL client | 9.5.0 | |
| Ollama | 0.34.4 | models on disk; server was down |
| ffmpeg | present | |
| ngrok | present | |
| SSH keys | `id_ed25519.pub`, others | |

AWS:

- Default region: `ap-south-1`
- Default identity: account `660442155240` as **root** (`arn:aws:iam::660442155240:root`)
- Profiles present: `default`, `codopilot`, `predixion`
- `predixion` profile has keys; region not set in that profile
- **Never provision billable resources without explicit approval**
- Prefer `--profile predixion` only if the assignment says so

GitHub:

- `gh auth status` OK outside sandbox (keyring)
- Account: `maannaan`
- Scopes: gist, read:org, repo, workflow

---

## 6. Workspace structure

```text
/Users/apple/Desktop/Steadfast-part 2/
  PREDIXION_FINAL_ROUND_CONTEXT.md   # this file
  EXECUTION_CHECKLIST.md             # live status + reusable checklist
  ENGINEERING_DECISIONS.md           # only real decisions
  IMPLEMENTATION_WALKTHROUGH.md      # component map matching source
  FOUNDER_DISCUSSION_PREP.md         # 10-min defense + Q&A
  .gitignore
  .git/                              # local repo only, no remote yet
```

Assignment source will be created here after 09:30. Do not pre-build feature folders.

---

## 7. Recommended development and testing workflow

1. Default Python: `python3.12` or `uv init --python 3.12`
2. Isolate deps: `uv venv && source .venv/bin/activate` (or `uv run`)
3. Never commit `.env`. Keep `.env.example`.
4. Core path first: smallest end-to-end slice, then tests, then polish.
5. Test order: smallest unit → related integration → full suite at checkpoints only.
6. Docker: confirm daemon before any compose/build (`docker info`).
7. Terraform: `fmt` + `validate` locally; `plan` before any apply; apply only with approval.
8. AWS: confirm account/profile/region before any API write.
9. If LLM/cloud creds missing: mock with the same interface, labeled as mock.

Credit rules for this engagement:

- Read this file and `EXECUTION_CHECKLIST.md` before broad scans.
- Targeted file inspection only.
- No speculative assignment implementation.
- No extra agents for routine work.

---

## 8. Useful commands

```bash
# Always start here
cd "/Users/apple/Desktop/Steadfast-part 2"

# Tool sanity
python3.12 --version
node -v && npm -v
git --version
docker info
terraform version
aws sts get-caller-identity
aws sts get-caller-identity --profile predixion
gh auth status

# Python project (typical)
uv init --python 3.12
uv add fastapi uvicorn pydantic httpx
uv add --dev pytest pytest-cov ruff
uv run pytest -q
uv run ruff check .

# Node project (typical)
npm init -y
npm test

# Docker
open -a Docker
docker compose up --build
docker compose down -v

# Terraform (local only until approved)
terraform fmt -recursive
terraform init
terraform validate
terraform plan -out=tfplan

# Git (local workspace only)
git status
git diff
git log --oneline -n 15
git add -A && git status   # inspect before commit

# GitHub (only after user asks to push / create repo)
gh repo create <name> --private --source=. --remote=origin
git push -u origin HEAD

# Logs / debug
docker compose logs -f --tail=100
```

Python venv without uv:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

---

## 9. Architecture principles (apply only when relevant)

- Working core first. No extra abstraction.
- Modular boundaries, env-based config, structured logs, input validation.
- Production patterns only if the problem needs them: timeouts, bounded retries, idempotency, health checks, metrics, least privilege, resource limits.
- AI: provider-independent interface, timeouts, fallback, structured output validation, cost/latency awareness. Mock must be labeled.
- Cloud: IaC, secrets out of git, public/private split, teardown documented, cost before provision.
- Submission must be understandable to an engineer who has not seen this chat.

---

## 10. Assignment execution strategy

On receipt of the assignment:

1. Extract: problem, mandatory vs optional, deliverables, tech constraints, evaluation criteria, submission method, deadline.
2. Plan P0 / P1 / P2. Build the smallest complete P0.
3. Record assumptions vs explicit requirements in this file.
4. Ask only if a missing fact blocks P0.
5. Implement, verify, then expand.
6. At 14:30 IST freeze features. At 14:50 IST submit.

Do not implement tonight. Wait for the real brief.

---

## 11. Submission checklist (high level)

See `EXECUTION_CHECKLIST.md` for the working list.

Minimum target unless the brief says otherwise:

- Working source
- Clear project layout
- README with setup / run / test / (deploy+teardown if cloud)
- `.env.example` if config is needed
- Automated tests + real results
- Known limitations honestly listed
- Git history that another engineer can follow
- Required artifact (GitHub repo / zip / etc.)

Never fabricate tests, screenshots, URLs, or metrics.

---

## 12. Known constraints and unresolved setup issues

P0 — handle before or at 09:30:

1. **Docker daemon.** Was down at first inspect; Docker.app started and daemon responded (`Server=29.6.1`, 8 CPUs, ~8 GB VM RAM). Re-check at 09:30: `docker info`. If it failed overnight, `open -a Docker`.
2. **Default `python3` is 3.9.6.** Always call `python3.12` or uv.
3. **Home directory git repo at `/Users/apple`.** Dangerous. Use only this workspace repo.
4. **No git remote yet.** Create only after the assignment repo name is known and user approves push.
5. **AWS default identity is root** on account `660442155240`. Confirm which account/profile the assignment requires before any write. `predixion` profile region is unset.
6. **kubectl has no current context.** Fine unless the brief needs a cluster.
7. **pytest/ruff/fastapi not installed globally.** Install per-project with uv. Do not preinstall.

P1 — install only if the assignment needs them:

- Helm: missing
- Ansible: missing
- wget: missing (`curl` is present)
- PostgreSQL client `psql`: missing (MySQL client is present)
- AWS SAM / CDK / eksctl / kind / minikube: missing
- pnpm / yarn: missing (`npm` is present)
- Poetry: missing (`uv` is present)

P2 / operational:

- Ollama installed with local models, but `ollama serve` was not running.
- Terraform 1.17.0 vs latest 1.17.1 — ignore unless a provider requires it.
- Java is Android Studio’s JBR, not a dedicated JDK install. Fine for most Java tasks; install Temurin only if the brief is Java-heavy.
- `gh` keyring auth failed inside some sandboxed shells; works in a normal terminal. If `gh` fails, retry outside sandbox or `gh auth refresh -h github.com`.

Do not brew-install extras tonight unless Manan asks.

---

## 13. Tomorrow 09:30 — exact start procedure

Manan:

1. Open this workspace in Cursor.
2. Start Docker Desktop if `docker info` fails. Start Ollama only if the brief needs local models: `ollama serve`.
3. Paste the full assignment text / PDF / screenshots into chat.
4. Say: `Switch to execution mode.`

Assistant (immediate):

1. Extract requirements into this file (problem, P0/P1/P2, deliverables, constraints, submission).
2. Write a short plan in `EXECUTION_CHECKLIST.md`.
3. Scaffold the real project in this directory.
4. Implement P0 end-to-end, then test, then P1.
5. Do not discuss theory past the first 30 minutes.

---

## 14. Live assignment log (fill after 09:30)

- Problem statement:
- Mandatory (P0):
- Important (P1):
- Optional (P2):
- Deliverables:
- Tech constraints:
- Evaluation criteria:
- Submission method:
- Assumptions:
- Decisions:
- Implemented and verified:
- Implemented, not verified:
- Partial:
- Not implemented:
- Known issues:
