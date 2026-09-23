# Architecture

```
                 GitHub Actions (CI on every PR)
                            |
                 docker build + pytest + terraform validate
                            |
                     workflow_dispatch
                            |
                    GHCR image :$SHA
                            |
                            v
Internet --> ALB :80 --> ECS Fargate (api:8000)
                            |
                            +--> ECS Fargate (worker)
                            |
                            v
                     RDS Postgres (private subnets)
                            |
                     CloudWatch logs + 5xx/CPU alarms
                            |
                     Discord webhook (after 3 failures)
```

## Why this shape

- **No NAT Gateway.** ECS tasks sit on public subnets with `assign_public_ip = true` so they can pull from GHCR. RDS stays private. Same-VPC traffic does not need NAT. This keeps a lab under ~US$ 8/month instead of ~US$ 40.
- **Two processes, one image.** API and worker share the Dockerfile. Worker overrides `command`. Production tags are git SHAs, never `latest`.
- **Secrets out of Git.** `DATABASE_URL` and the Discord webhook live in SSM Parameter Store and are injected into the task definition.
- **Least privilege.** Execution role can read SSM + pull images + write logs. Task role only writes logs. RDS security group accepts 5432 only from the ECS security group.
- **Health checks at two layers.** ALB hits `/health`. ECS container health check hits localhost. A process bound to `127.0.0.1` would pass the container check and fail the ALB — that is a documented footgun in RUNBOOK.md.

## What Kubernetes would add

Nothing this size needs a cluster. The next honest step is a second environment (`staging` / `prod`) with Terraform workspaces, then EKS when there is more than one team deploying.
