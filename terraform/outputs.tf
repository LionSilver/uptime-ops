output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "HTTP URL of the API"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "rds_endpoint" {
  description = "RDS endpoint (hostname only)"
  value       = aws_db_instance.main.address
  sensitive   = true
}

output "log_group" {
  description = "CloudWatch log group"
  value       = aws_cloudwatch_log_group.main.name
}

output "ssm_database_url" {
  description = "SSM parameter name for DATABASE_URL"
  value       = aws_ssm_parameter.database_url.name
}
