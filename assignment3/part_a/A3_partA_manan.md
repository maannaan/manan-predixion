# Assignment 3, Part A — Fix and Ship

## A1. Defects

Line numbers refer to the original snippet, counting `import os, time, ...` as line 1.

| # | Line | Code | What goes wrong in production | Severity | Fix |
|---|---|---|---|---|---|
| 1 | 27 | `if disposition == "NO_ANSWER" or "BUSY":` | Parsed as `(disposition == "NO_ANSWER") or "BUSY"`; `"BUSY"` is truthy, so it's **always true**. Every call gets a retry, including PTP, DISPUTE and WRONG_NUMBER. Borrowers who already promised or disputed get called again: compliance and harassment risk. | High | `if disposition in {"NO_ANSWER", "BUSY"}:` |
| 2 | 13 | `if attempt > len(RETRY_GAPS_MIN)` | Off-by-one: `attempt == 3` passes, then `RETRY_GAPS_MIN[3]` raises `IndexError`, so the webhook returns 500. The voice platform retries the webhook, and each retry inserts a duplicate row. | High | `>=`; also reject negative `attempt` (`[-1]` silently picks 240). |
| 3 | 15 | `datetime.now()` | Naive server time. Containers run in **UTC**, so the 08:00–19:00 IST check is off by 5 h 30 m and calls land at night IST. | High | `datetime.now(ZoneInfo("Asia/Kolkata"))`, and pass `now` in so it's testable. |
| 4 | 16 | `next_time.hour > 19` | 19:00–19:59 passes (`19 > 19` is false), so calls are scheduled after 19:00. There's also no check for **before 08:00**: a 23:00 call + 240 min gives 03:00. | High | Compare `.time() >= 19:00` and `.time() < 08:00`. |
| 5 | 17 | `.replace(hour=9) + timedelta(days=1)` | Keeps minutes and seconds (09:47:13), uses 09:00 when the window opens at 08:00, and only ever moves to the next day. | Medium | Move to 08:00:00 the same day (early) or the next day (late). |
| 6 | 25 | f-string `INSERT` | **SQL injection**: `account_id` comes from the request body. An `account_id` like `x'); DROP TABLE calls;--` is executed. Quotes in data also break the insert. | High | Parameterised query: `execute("... VALUES (?, ?, ?)", (a, d, n))`. |
| 7 | 6 | `DB = sqlite3.connect("calls.db")` | One connection shared by all requests (SQLite isn't safe for that). The file lives on the container's disk, so it's **lost on every redeploy** and **not shared between tasks** behind a load balancer. | High | Managed database (RDS Postgres or DynamoDB) with a connection pool. |
| 8 | 25 | no `DB.commit()` | The insert is never committed, so rows are lost when the process exits. Works on a laptop if you check from the same connection. | High | Commit, or a `with conn:` transaction. |
| 9 | 35 | `"next_call": nxt` (a `datetime`) | `datetime` isn't JSON-serialisable, so `requests` raises `TypeError`. The bare `except` swallows it and tries 5 times, so **the CRM never receives any retry**. | High | `nxt.isoformat()` (includes `+05:30`). |
| 10 | 35 | `timeout=None` | When the CRM hangs, the request waits forever and the worker is stuck. | High | Timeout of a few seconds. |
| 11 | 35, 38 | `requests.post` / `time.sleep` inside `async def` | Blocking calls in an async handler **freeze the event loop**: one slow CRM call stalls every request on that worker. | High | `httpx.AsyncClient` + `asyncio.sleep`, or better, enqueue to SQS. |
| 12 | 37 | bare `except:` | Catches everything, including the `TypeError` above, and logs nothing. After 5 failures it returns `None`, the handler returns `ok`, and the retry is **silently lost**. | High | Catch specific network errors, log them, raise or dead-letter after the last try. |
| 13 | 36 | `return r.json()` with no status check | A 500 or HTML error page from the CRM either "succeeds" or raises inside the loop and **re-posts a request that may already have been processed** (duplicates). | Medium | `r.raise_for_status()`; send an idempotency key. |
| 14 | 33–38 | 5 tries × 1 s | The CRM is "sometimes down for minutes"; 5 seconds of retries doesn't cover that. | Medium | Exponential backoff with jitter for short blips; a durable queue (SQS + DLQ) for long outages. |
| 15 | 29 | `notify_crm(account_id, nxt)` when `nxt is None` | After the last attempt, the CRM is told `next_call: null`, which may clear or break its schedule. | Medium | Only notify when `nxt` is not `None` (or send an explicit "no more retries" event). |
| 16 | 22–24 | `body["account_id"]`, `.get(...)` | No validation: a missing key gives `KeyError` → 500, and `attempt` can be a string. | Medium | Pydantic request model (`account_id: str`, `disposition: Literal[...]`, `attempt: int >= 0`). |
| 17 | 20 | the whole endpoint | No **webhook authentication**: anyone who finds the URL can insert rows and trigger calls. | High | Verify the voice platform's signature (HMAC) or a shared secret; restrict at the ALB/WAF. |
| 18 | 20–30 | the whole endpoint | Not **idempotent**: voice platforms redeliver webhooks, so one call produces duplicate rows and duplicate retries. | Medium | Unique `call_id` in the table; skip if already processed. |
| 19 | 11 | `history=[]` | Mutable default argument, created once and shared by every call. It grows forever (memory leak) and isn't used. | Low | Remove it (or `history=None`). |
| 20 | 7 | `os.getenv("CRM_URL")` | If unset, it's `None`, `requests.post(None)` fails, and the bare `except` hides it. The service looks healthy but does nothing. | Medium | Fail fast at startup if missing (Pydantic settings). |
| 21 | 25–29 | DB write, then CRM call | No transaction between the two: if the CRM call fails the row exists but the retry doesn't. | Medium | Outbox pattern, or enqueue to SQS in the same request and let a worker deliver. |
| 22 | 25 | `INSERT INTO calls` | Table is never created, so first run on a fresh environment fails. | Low | Migration at deploy time. |

Not a bug: `notify_crm` is defined after the handler. Python looks the name up when the handler runs, by which time it exists.

### Corrected code

Full version with tests in `A3_partA_manan.py` / `test_A3_partA_manan.py`.

```python
IST = ZoneInfo("Asia/Kolkata")
RETRY_GAPS_MIN = [30, 120, 240]   # gap before attempt 1, 2, 3
WINDOW_START, WINDOW_END = time(8, 0), time(19, 0)
RETRYABLE = {"NO_ANSWER", "BUSY"}

def schedule_retry(attempt: int, now: datetime | None = None) -> datetime | None:
    if attempt < 0:
        raise ValueError(f"attempt must be >= 0, got {attempt}")
    if attempt >= len(RETRY_GAPS_MIN):
        return None
    now = (now or datetime.now(tz=IST)).astimezone(IST)
    next_time = now + timedelta(minutes=RETRY_GAPS_MIN[attempt])
    if next_time.time() < WINDOW_START:
        next_time = next_time.replace(hour=8, minute=0, second=0, microsecond=0)
    elif next_time.time() >= WINDOW_END:
        next_time = (next_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    return next_time
```

```python
    # handler, after the parameterised insert
    if call.disposition in RETRYABLE:
        next_call = schedule_retry(call.attempt)
        if next_call is not None:
            await notify_crm(call.account_id, next_call)   # production: send to SQS instead
```

**Assumption:** `attempt` is the attempt that just finished, with the first call = 0, so the gap before the next attempt is `RETRY_GAPS_MIN[attempt]`. IST has no daylight saving, so `replace(hour=8)` is safe.

## A2. AWS short answers

### 1. Production architecture (ap-south-1)

```
Voice platform
     │ HTTPS webhook (HMAC-signed)
     ▼
Route 53 ──► WAF ──► ALB (public subnets, ACM cert, 2–3 AZs)
                       │
                       ▼
          ECS Fargate: webhook API (private subnets, autoscaling)
             │ validate, write, enqueue, return 200
     ┌───────┴─────────────┐
     ▼                     ▼
RDS Postgres          SQS crm-retry queue ──► DLQ (alarm)
(Multi-AZ, KMS,            │
 RDS Proxy)                ▼
                 ECS Fargate: CRM worker ──(NAT)──► CRM
                 backoff, idempotency key

Secrets Manager + KMS: DB creds, CRM key, webhook secret
CloudWatch Logs/metrics/alarms, CloudTrail
VPC endpoints: ECR, Logs, SQS, Secrets Manager
```

- **ALB + WAF:** TLS termination, health checks, spreads 500 rps across tasks; WAF rate-limits and allows only the voice platform's IPs.
- **ECS Fargate in private subnets, multi-AZ:** stateless containers, no servers to patch, scales on `RequestCountPerTarget`. A handful of tasks handles 500 rps because the handler only writes and enqueues.
- **RDS Postgres Multi-AZ + RDS Proxy:** durable call records with a unique `call_id` for idempotency; the proxy pools connections when tasks scale out.
- **SQS + DLQ for the CRM:** this is the answer to "CRM is down for minutes". The webhook doesn't wait for the CRM; messages wait in the queue (retention up to 14 days) and the worker retries with backoff. Anything that fails repeatedly lands in the DLQ with an alarm.
- **PII stays in India:** every resource is in ap-south-1, encrypted with KMS keys in that region, and backups stay in-region (DR, if needed, goes to ap-south-2 Hyderabad). An SCP denies other regions, and logs don't contain phone numbers (masked).
- **Secrets Manager:** credentials are never in the image or env files.
- **VPC endpoints:** ECR, Logs, SQS and Secrets Manager traffic stays off the internet and reduces NAT costs. Only the CRM worker needs NAT.

### 2. Task role vs task execution role

- **Task execution role:** used by the **ECS agent** before your code starts: pull the image from ECR, create log streams in CloudWatch, and fetch secrets referenced in the task definition's `secrets` block.
- **Task role:** assumed by **your application code** at runtime for its own AWS calls (send to SQS, read a secret through the SDK, write to DynamoDB).

Least-privilege statement to read one secret. It goes on the execution role if the secret is injected through the task definition, or on the task role if the code reads it with the SDK:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-south-1:123456789012:secret:prod/crm-api-key-AbCdEf"
    }
  ]
}
```

Secrets Manager adds a random 6-character suffix to ARNs, so use the full ARN (or `prod/crm-api-key-??????`). If the secret uses a customer-managed KMS key, also allow `kms:Decrypt` on that key with a `kms:ViaService = secretsmanager.ap-south-1.amazonaws.com` condition.

### 3. 5xx spike right after a deploy

1. **Roll back first if users are affected, diagnose second.** With the deployment circuit breaker and rollback enabled, ECS may already be rolling back. Otherwise point the service at the previous task definition: `aws ecs update-service --cluster prod --service webhook --task-definition webhook:41` (or redeploy the previous image tag through the pipeline).
2. **Which 5xx?** `HTTPCode_ELB_5XX` (502/503/504: no healthy targets, tasks crashing, timeouts) vs `HTTPCode_Target_5XX` (the app is returning errors).
3. **Target group health and ECS service events:** are new tasks failing health checks, or stopping? Check `stoppedReason`: out of memory, essential container exited, `CannotPullContainerError`, failure to fetch a secret.
4. **CloudWatch logs for the new task definition revision:** stack traces, missing environment variables, failed DB connections, a migration that didn't run.
5. **What changed besides code:** security groups, IAM role permissions, secret values, a DB migration, a dependency (CRM) that was down at the same time.
6. **Verify recovery:** 5xx back to baseline, then postmortem. Prevent it next time with CloudWatch alarms in the deployment config (automatic rollback on a 5xx alarm), a canary or blue/green deploy, and backward-compatible migrations so rollback is always safe.

### 4. Lambda + API Gateway vs ECS Fargate

**Pick Lambda + API Gateway when:**
- Traffic is low, spiky or unpredictable, and scaling to zero saves money.
- Each request is short and stateless.
- The team wants no containers to manage.

**Lambda's limits to watch:**
- Cold starts.
- Account concurrency limits, which slow CRM calls eat into.
- The API Gateway integration timeout.
- Database connection storms, which need RDS Proxy.
- Per-request pricing, which adds up at sustained high traffic.

**Pick ECS Fargate when:**
- Traffic is steady and high.
- You want long-lived connection pools to the database.
- Latency needs to be predictable, without cold starts.
- The service is already a container.

**For this service I'd pick Fargate.** It peaks at 500 rps, keeps a DB connection pool, and Part B already ships a container.

**Hybrid option:** the SQS → CRM retry worker fits Lambda well, using an SQS event source with batching. It's low volume, event-driven, and Lambda's built-in retry and DLQ handling come for free.