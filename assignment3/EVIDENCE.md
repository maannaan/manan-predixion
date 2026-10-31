# Assignment 3 evidence

Nothing below is invented.

## Tests

```text
cd assignment3 && pytest
7 passed
```

Includes `schedule_retry` at 07:30, 18:45, and 23:00 IST.

## Terraform

```text
terraform init   # aws provider 5.100.0
terraform validate
# Success! The configuration is valid.

terraform plan
# Plan: 31 to add, 0 to change, 0 to destroy.
```

`terraform apply` was **not** run. There is **no** live `/health` URL.

## Docker

Docker daemon was not running on this machine at verification time (`docker info` failed). Image was not built. Start Docker Desktop, then:

```bash
docker build -t call-webhook .
docker run --rm -p 8080:8080 call-webhook
curl -s http://127.0.0.1:8080/health
```
