# Cloud Deployment Patterns

InvoiceBridge API is designed to be portable across managed container platforms, but the primary architecture target is single-cloud multi-region. Multi-cloud should only be used when a customer, regulator, procurement process, or vendor-risk policy requires it.

## AWS Pattern

| Concern | AWS service fit |
| --- | --- |
| Container runtime | ECS Fargate or App Runner |
| Image registry | ECR |
| Regional database | RDS PostgreSQL primary plus cross-region read replica / promoted standby |
| Traffic failover | Route 53 health checks, AWS Global Accelerator, or ALB plus DNS routing |
| Secrets | AWS Secrets Manager or SSM Parameter Store |
| Logs/metrics | CloudWatch Logs, CloudWatch metrics, OpenTelemetry collector if added |
| Migrations | One explicit Alembic migration job before app rollout |
| Smoke tests | `/health/ready`, `/v1/regions`, tenant region decision, validate, transform, send, audit trail |

Recommended AWS shape:

```text
ECR image
  -> ECS Fargate service in eu-west-1
  -> ECS Fargate service in eu-central-1
  -> RDS PostgreSQL regional primary + promoted standby path
  -> Route 53 health-based failover
```

## GCP Pattern

| Concern | GCP service fit |
| --- | --- |
| Container runtime | Cloud Run in two regions |
| Image registry | Artifact Registry |
| Regional database | Cloud SQL PostgreSQL primary plus cross-region replica / promoted standby |
| Traffic failover | External HTTP(S) Load Balancer with serverless NEGs or DNS failover |
| Secrets | Secret Manager |
| Logs/metrics | Cloud Logging, Cloud Monitoring, OpenTelemetry collector if added |
| Migrations | One explicit Alembic migration job before app rollout |
| Smoke tests | `/health/ready`, `/v1/regions`, tenant region decision, validate, transform, send, audit trail |

Recommended GCP shape:

```text
Artifact Registry image
  -> Cloud Run service in europe-west1
  -> Cloud Run service in europe-west3
  -> Cloud SQL PostgreSQL regional primary + promoted standby path
  -> Global HTTPS Load Balancer / DNS failover
```

## Skills Demonstrated

- Containerized FastAPI runtime with cloud-neutral configuration.
- PostgreSQL persistence with Alembic migrations.
- Regional tenant routing through `home_region`, `data_residency_region`, and `failover_region`.
- Regional-primary writes instead of risky active-active database writes.
- Standby write protection through `REGION_ROLE`.
- Idempotency keys for retry-safe transform/send operations.
- Regional audit trails with processing-region evidence.
- Health/readiness checks and smoke-testable deployment topology.
- ADR-backed tradeoff explanation for multi-region before multi-cloud.

## What Is Not Claimed

- No Terraform modules are included yet.
- No AWS or GCP production deployment is currently provisioned by this repository.
- No managed database replication is simulated locally.
- Tenant-scoped API keys are implemented, but no full account-management, key-rotation, or IAM integration is included yet.
