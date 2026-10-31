# Assignment 3 — Fix and Ship (Part B)

Production webhook service. **Part B imports the corrected `schedule_retry` / CRM notify / retryable dispositions from `part_a/A3_partA_manan.py`.** Do not edit Part A from the assistant.

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

[`.github/workflows/assignment3.yml`](../.github/workflows/assignment3.yml) — tests on PR/push; image push uses AWS OIDC when `AWS_OIDC_ROLE_ARN` is set; `terraform apply` only on `workflow_dispatch` with `deploy=true`.
