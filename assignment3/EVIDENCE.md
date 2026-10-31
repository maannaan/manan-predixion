# Assignment 3 evidence

Nothing below is invented. Account `660442155240`, region `ap-south-1`. Tear down within 24 hours.

## Local Docker

```text
docker build -t call-webhook:local .
docker run --rm -p 8080:8080 call-webhook:local
curl -sS http://127.0.0.1:8080/health
{"status":"ok"}
```

Uvicorn log: `GET /health HTTP/1.1" 200 OK`

## Terraform

```text
terraform apply
Apply complete! Resources: 31 added, 0 changed, 0 destroyed.
```

## Live service

- ALB: `predixion-call-webhook-alb-1459486561.ap-south-1.elb.amazonaws.com`
- Health: http://predixion-call-webhook-alb-1459486561.ap-south-1.elb.amazonaws.com/health
- `curl` result: HTTP 200 `{"status":"ok"}`
- ECR: `660442155240.dkr.ecr.ap-south-1.amazonaws.com/predixion-call-webhook:latest`

## GitHub Actions

- `test` runs on push/PR. That is the required check.
- `build-and-push` uses AWS OIDC (`secrets.AWS_OIDC_ROLE_ARN`). The secret is not set, so that job is skipped instead of failing. Image was pushed locally to ECR.
- Account already has `token.actions.githubusercontent.com` OIDC provider. Live deploy used local `terraform apply` + `docker push`, not Actions.

## Teardown (do this today)

```bash
cd assignment3/terraform
AWS_PROFILE=default terraform destroy -auto-approve
```
