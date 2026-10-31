# manan-predixion

Private submission for Predixion AI engineering assignments (Manan Paliwal). Python 3.12.

Part A lives in `assignmentN/part_a/` (candidate-owned, not edited by AI). Part B uses it where the brief says to: A3 imports `schedule_retry` / `notify_crm`; A4 loads the rewritten system prompt. A1 ledger implements the A3.4 unique `gateway_txn_id` rule; A2 analysis is a separate extract from Part A’s capacity/A/B/funnel.

## Run each Part B

```bash
# 1 Collections ledger
cd assignment1 && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pytest

# 2 Dialer analytics
cd assignment2 && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python analyze.py && pytest

# 3 Webhook
cd assignment3 && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pytest
# docker build/run when Docker Desktop is up
# live: http://predixion-call-webhook-alb-1459486561.ap-south-1.elb.amazonaws.com/health

# 4 Collections agent
cd assignment4 && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python eval.py && pytest
```

## Assignment 3 AWS (ap-south-1)

Full labels, IAM split, and teardown: [`assignment3/README.md`](assignment3/README.md).

Internet never reaches the tasks. The ALB is public; Fargate runs in private subnets and talks to the CRM through NAT. `CRM_URL` comes from Secrets Manager at task start.

```mermaid
flowchart TB
  Voice[Voice platform / reviewer]
  subgraph aws ["ap-south-1 · VPC 10.80.0.0/16"]
    ALB[ALB :80 public subnets]
    ECS[ECS Fargate x2 private subnets]
    NAT[NAT Gateway]
    ECR[ECR]
    SM[Secrets Manager CRM_URL]
    CW[CloudWatch logs]
  end
  Voice --> ALB --> ECS
  ECS --> CW
  ECS --> SM
  ECS --> NAT
  ECR -.-> ECS
```

```mermaid
sequenceDiagram
  actor Client
  participant ALB
  participant Task
  participant CRM
  Client->>ALB: POST /webhook/call-completed or GET /health
  ALB->>Task: :8080
  alt call-completed and NO_ANSWER / BUSY
    Task->>Task: schedule_retry in IST
    Task->>CRM: notify with backoff
  end
  Task-->>Client: 200
```
