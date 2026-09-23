# Runbook

Three incidents this lab is designed to survive. Each one is a story you can tell in an interview.

## 1. API returns 5xx behind the ALB

**Symptoms:** CloudWatch alarm `uptime-ops-alb-5xx`. Browser on the ALB DNS shows 502/503.

**Hypotheses (in order):**
1. Task never passed `/health` (wrong bind address, crash loop).
2. Security group does not allow ALB → task:8000.
3. Image pull failed (GHCR package is private, or tag does not exist).

**Commands:**
```bash
aws ecs list-tasks --cluster uptime-ops --service-name uptime-ops-api
aws ecs describe-tasks --cluster uptime-ops --tasks <id>
aws logs tail /ecs/uptime-ops --follow --since 15m
curl -sS http://<alb-dns>/health
```

**Lab incident (real):** first ALB health check failed because a draft of the app listened on `127.0.0.1:8000`. Uvicorn now binds `0.0.0.0`. Container health checks localhost; the load balancer does not.

## 2. Worker stopped pinging

**Symptoms:** targets stay `unknown`, no new rows in `/targets/{id}/checks`.

**Hypotheses:**
1. Worker service desired count is 0 or tasks are crash-looping.
2. `DATABASE_URL` in SSM is wrong (password rotated, host changed).
3. Discord webhook raises and the loop dies — the worker catches this and logs; check the `worker` log stream.

**Commands:**
```bash
aws ecs describe-services --cluster uptime-ops --services uptime-ops-worker
aws logs tail /ecs/uptime-ops --log-stream-name-prefix worker --follow
```

**Mitigation:** force a new deployment of the worker service. Confirm `CHECK_INTERVAL_SECONDS` and `FAILURE_THRESHOLD`.

## 3. AWS bill climbing

**Symptoms:** budget alarm at 80% of US$ 8.

**Hypotheses:** RDS left running over the weekend, extra NAT (this stack has none), ALB + Fargate idle hours.

**Mitigation:**
```bash
# GitHub → Actions → destroy → Run workflow
# or locally:
terraform -chdir=terraform destroy -auto-approve
```

Never leave a lab stack up "to look at later". Screenshot, record the 40s demo, destroy.
