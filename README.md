# uptime-ops

Sample de portfólio DevOps: monitor de uptime em estilo produção.

**Stack:** FastAPI · Postgres · Docker · ECS Fargate · ALB · Terraform · GitHub Actions · GHCR · CloudWatch · Discord alerts

---

## O que este projeto demonstra

| Prática | Como aparece aqui |
|---------|-------------------|
| App containerizado | Dockerfile multi-stage, usuário não-root, tag imutável por SHA |
| Local = próximo de prod | `docker compose` com API + worker + Postgres + Prometheus |
| Infra como código | Terraform (VPC, ECS, ALB, RDS, SSM, IAM, alarmes) |
| Sem NAT (custo) | Tasks em subnet pública com `assign_public_ip`; RDS privado |
| Segredos fora do Git | `DATABASE_URL` e Discord webhook no SSM Parameter Store |
| Least privilege | Execution role (SSM + pull + logs) ≠ task role (só logs) |
| CI | lint + pytest + `terraform validate` + build/push GHCR |
| CD | Deploy e destroy via `workflow_dispatch` |
| Observabilidade | `/health`, `/metrics`, CloudWatch logs + alarmes 5xx/CPU |
| Runbook | Três incidentes reais com hipóteses e comandos |

Documentação extra:
- [ARCHITECTURE.md](./ARCHITECTURE.md) — por que essa forma
- [RUNBOOK.md](./RUNBOOK.md) — como responder a 5xx, worker parado e conta subindo

---

## Arquitetura (resumo)

```
GitHub Actions (CI) ──► GHCR :$SHA
         │
         ▼  workflow_dispatch (deploy)
Internet ──► ALB :80 ──► ECS Fargate (api:8000)
                              │
                              ├── ECS Fargate (worker)
                              ▼
                         RDS Postgres (privado)
                              │
                         CloudWatch + Discord (após 3 falhas)
```

---

## Rodar local

```bash
# API em :8080, Postgres, worker e Prometheus
make up

curl http://localhost:8080/health
# {"status":"ok"}

# criar um target
curl -X POST http://localhost:8080/targets \
  -H 'Content-Type: application/json' \
  -d '{"name":"example","url":"https://example.com"}'

make down   # para e remove volumes
```

Testes e lint:

```bash
make lint
make test
```

---

## Deploy na AWS (lab)

### Pré-requisitos

1. Conta AWS + IAM user com permissões para VPC, ECS, RDS, ALB, IAM, SSM, CloudWatch
2. Secrets no repositório GitHub:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `DISCORD_WEBHOOK_URL` (opcional)
3. Variable opcional: `AWS_REGION` (default `us-east-1`)

### Fluxo

1. **Push na `main`** → CI roda testes, valida Terraform e **publica a imagem** em  
   `ghcr.io/<owner>/uptime-ops:<sha>`
2. **Actions → deploy → Run workflow**  
   (opcional: informar um SHA; senão usa o commit atual)
3. No summary do job aparece a URL do ALB
4. Quando terminar o demo: **Actions → destroy → Run workflow**

Custo estimado do lab (ligado): **~US$ 5–10/mês**. Destrua quando não estiver usando.

### Deploy local (opcional)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# edite image= e discord_webhook_url=

terraform init
terraform plan
terraform apply
```

---

## Estrutura do repositório

```
.
├── app/                    # FastAPI + worker
│   ├── Dockerfile
│   ├── src/uptime_ops/
│   └── tests/
├── terraform/              # IaC (VPC, ECS, ALB, RDS, SSM, IAM…)
├── .github/workflows/
│   ├── ci.yml              # test + build/push GHCR + terraform validate
│   ├── deploy.yml          # terraform apply (manual)
│   └── destroy.yml         # terraform destroy (manual)
├── docker-compose.yml      # ambiente local
├── ARCHITECTURE.md
├── RUNBOOK.md
└── Makefile
```

---

## Licença

MIT — veja [LICENSE](./LICENSE).
