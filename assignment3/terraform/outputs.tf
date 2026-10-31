output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "health_url" {
  value = "http://${aws_lb.this.dns_name}/health"
}
