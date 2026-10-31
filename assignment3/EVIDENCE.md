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

- `test` runs on push/PR.
- **Run workflow** runs `build-and-push` then `deploy` (ECS force-new-deployment). OIDC role `predixion-call-webhook-gha`. Repo secret `AWS_OIDC_ROLE_ARN` is set.
- `terraform apply` is local only. CI must not apply: state is `assignment3/terraform/terraform.tfstate` on this laptop, not a remote backend.

## Teardown (do this today)

```bash
cd assignment3/terraform
AWS_PROFILE=default terraform destroy -auto-approve
```
