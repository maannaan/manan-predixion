# Assignment 3 — Fix and Ship (Part B)

Production webhook service. **Part A was not supplied** (`part_a/` has no candidate answers). This folder is Part B only and does not claim Part A is complete.

## App

- FastAPI + Pydantic `CallCompleted`
- `GET /health`
- JSON logs
- `schedule_retry` in IST, window 08:00–19:00, gaps `[30, 120, 240]` minutes
- Parameterized SQLite inserts; CRM notify with timeout and 3 attempts

```bash
cd assignment3
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --port 8080
```

## Docker

```bash
docker build -t call-webhook .
docker run --rm -p 8080:8080 call-webhook
curl -s http://127.0.0.1:8080/health
```

## Terraform (do not apply unless approved)

ECS Fargate in private subnets, ALB, ECR, Secrets Manager `CRM_URL`, CloudWatch logs, request-count autoscaling, deployment circuit breaker + rollback.

```bash
cd terraform
terraform init
terraform validate
terraform plan
```

No `terraform apply` has been run. There is no live URL.

## CI

[`.github/workflows/assignment3.yml`](../.github/workflows/assignment3.yml) — tests on PR/push; image push uses AWS OIDC; `terraform apply` only on `workflow_dispatch` with `deploy=true`.
