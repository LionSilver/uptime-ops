resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_ssm_parameter" "database_url" {
  name        = "/${var.project}/database_url"
  description = "PostgreSQL connection string for uptime-ops"
  type        = "SecureString"
  value       = "postgresql+psycopg://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.address}:5432/${var.db_name}"

  tags = {
    Name = "${var.project}-database-url"
  }
}

resource "aws_ssm_parameter" "discord_webhook" {
  name        = "/${var.project}/discord_webhook_url"
  description = "Discord webhook URL for uptime alerts"
  type        = "SecureString"
  value       = var.discord_webhook_url != "" ? var.discord_webhook_url : "disabled"

  tags = {
    Name = "${var.project}-discord-webhook"
  }
}
