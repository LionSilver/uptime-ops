variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "uptime-ops"
}

variable "environment" {
  description = "Environment name (lab, staging, prod)"
  type        = string
  default     = "lab"
}

variable "image" {
  description = "Full container image reference (e.g. ghcr.io/lionsilver/uptime-ops:abc123)"
  type        = string
}

variable "discord_webhook_url" {
  description = "Discord webhook URL for alerts (leave empty to disable)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "uptime"
}

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "uptime"
}

variable "check_interval_seconds" {
  description = "Worker check interval"
  type        = number
  default     = 30
}

variable "failure_threshold" {
  description = "Consecutive failures before Discord alert"
  type        = number
  default     = 3
}

variable "api_cpu" {
  description = "Fargate CPU units for API (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Fargate memory (MiB) for API"
  type        = number
  default     = 512
}

variable "worker_cpu" {
  description = "Fargate CPU units for worker"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Fargate memory (MiB) for worker"
  type        = number
  default     = 512
}

variable "desired_count_api" {
  description = "Desired count for API service"
  type        = number
  default     = 1
}

variable "desired_count_worker" {
  description = "Desired count for worker service"
  type        = number
  default     = 1
}
