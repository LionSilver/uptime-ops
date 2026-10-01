resource "aws_ecs_cluster" "main" {
  name = var.project

  setting {
    name  = "containerInsights"
    value = "disabled" # keep cost low for a lab
  }

  tags = {
    Name = var.project
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# ---------------------------------------------------------------------------
# Shared container definition fragments
# ---------------------------------------------------------------------------

locals {
  common_env = [
    {
      name  = "CHECK_INTERVAL_SECONDS"
      value = tostring(var.check_interval_seconds)
    },
    {
      name  = "FAILURE_THRESHOLD"
      value = tostring(var.failure_threshold)
    },
    {
      name  = "LOG_LEVEL"
      value = "INFO"
    },
  ]

  common_secrets = [
    {
      name      = "DATABASE_URL"
      valueFrom = aws_ssm_parameter.database_url.arn
    },
    {
      name      = "DISCORD_WEBHOOK_URL"
      valueFrom = aws_ssm_parameter.discord_webhook.arn
    },
  ]

  log_configuration = {
    logDriver = "awslogs"
    options = {
      "awslogs-group"         = aws_cloudwatch_log_group.main.name
      "awslogs-region"        = var.aws_region
      "awslogs-stream-prefix" = "ecs"
    }
  }
}

# ---------------------------------------------------------------------------
# API task definition
# ---------------------------------------------------------------------------

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.image
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = local.common_env
      secrets     = local.common_secrets

      # Container health check hits localhost (documented footgun in RUNBOOK).
      # ALB health check hits /health from the outside.
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')\" || exit 1"]
        interval    = 15
        timeout     = 5
        retries     = 3
        startPeriod = 20
      }

      logConfiguration = merge(local.log_configuration, {
        options = merge(local.log_configuration.options, {
          "awslogs-stream-prefix" = "api"
        })
      })
    }
  ])

  tags = {
    Name = "${var.project}-api"
  }
}

# ---------------------------------------------------------------------------
# Worker task definition (same image, different command)
# ---------------------------------------------------------------------------

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.image
      essential = true
      command   = ["python", "-m", "uptime_ops.worker"]

      environment = local.common_env
      secrets     = local.common_secrets

      logConfiguration = merge(local.log_configuration, {
        options = merge(local.log_configuration.options, {
          "awslogs-stream-prefix" = "worker"
        })
      })
    }
  ])

  tags = {
    Name = "${var.project}-worker"
  }
}

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

resource "aws_ecs_service" "api" {
  name            = "${var.project}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count_api
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true # required: no NAT Gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]

  lifecycle {
    ignore_changes = [desired_count] # allow manual scaling without Terraform drift
  }

  tags = {
    Name = "${var.project}-api"
  }
}

resource "aws_ecs_service" "worker" {
  name            = "${var.project}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.desired_count_worker
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    Name = "${var.project}-worker"
  }
}
