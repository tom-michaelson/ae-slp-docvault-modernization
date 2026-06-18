# ECR Repository
resource "aws_ecr_repository" "api_repo" {
  name                 = "agentic-workflow-accelerator-api-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "ui_repo" {
  name                 = "agentic-workflow-accelerator-ui-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}


# ECS Cluster
resource "aws_ecs_cluster" "app_cluster" {
  name = "${var.application_name}-${var.environment}-cluster"
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.application_name}-${var.environment}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_secret_policy" {
  name = "${var.application_name}-${var.environment}-ecs-secret-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/${var.environment}/${var.application_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = aws_kms_key.ssm_parameters.arn
      }
    ]
  })
}

# S3 Bucket for artifacts
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.application_name}-${var.environment}-artifacts"

  tags = {
    Name        = "${var.application_name}-${var.environment}-artifacts"
    Environment = var.environment
  }
}

#ECS Task Definition
resource "aws_ecs_task_definition" "app_task" {
  family                   = "${var.application_name}-${var.environment}-task"
  cpu                      = "1024"
  memory                   = "2048"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "agentic-workflow-accelerator-ui-${var.environment}"
      image = "${aws_ecr_repository.ui_repo.repository_url}:latest"
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name
          awslogs-region        = "${var.region}"
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "COGNITO_REGION"
          value = "${var.region}"
        },
        {
          name  = "PUBLIC_AUTH_MODE"
          value = "cognito"
        },
        { name = "PYTHONPYCACHEPREFIX", value = "./.cache/pycache" },
        { name = "DEBUG_MODE", value = "true" },
        { name = "TEMPORAL_VERSION", value = "1.27.2" },
        { name = "TEMPORAL_ADMINTOOLS_VERSION", value = "1.27.2-tctl-1.18.2-cli-1.3.0" },
        { name = "TEMPORAL_UI_VERSION", value = "2.34.0" },
        { name = "POSTGRESQL_VERSION", value = "16" },
        { name = "POSTGRES_PASSWORD", value = "temporal" },
        { name = "POSTGRES_USER", value = "temporal" },
        { name = "POSTGRES_DEFAULT_PORT", value = "5432" },
        { name = "TEMPORAL_UI_HOST", value = "localhost" },
        { name = "TEMPORAL_UI_PORT", value = "8002" },
        { name = "TEMPORAL_SERVER_HOST", value = "localhost" },
        { name = "TEMPORAL_SERVER_PORT", value = "7233" },
        { name = "TEMPORAL_METRICS_PORT", value = "8004" },
        { name = "AWA_UI_HOST", value = "0.0.0.0" },
        { name = "AWA_UI_PORT", value = "8000" },
        { name = "AWA_API_HOST", value = "localhost" },
        { name = "AWA_API_PORT", value = "8001" },
        { name = "HOME_DIR", value = "/app" },
        { name = "LITE_LLM_HOST", value = "localhost" },
        { name = "LITE_LLM_API_KEY", value = "sk-awa" },
        { name = "LANGFUSE_SECRET_KEY", value = "the_secret_key" },
        { name = "LANGFUSE_PUBLIC_KEY", value = "the_public_key" },
        { name = "LANGFUSE_HOST", value = "http://localhost:3001" },
        { name = "API_KEY", value = "sk-awa" }
      ],
      secrets = [
        # Auth
        # {
        #   valueFrom = "/${var.environment}/${var.application_name}/AUTH_MODE"
        #   name      = "AUTH_MODE"
        # },
        # Cognito Parameters
        {
          valueFrom = "/${var.environment}/${var.application_name}/AUTH_COGNITO_CLIENT_ID"
          name      = "AUTH_COGNITO_CLIENT_ID"
        },
        {
          valueFrom = "/${var.environment}/${var.application_name}/AUTH_COGNITO_CLIENT_SECRET"
          name      = "AUTH_COGNITO_CLIENT_SECRET"
        },
        {
          valueFrom = "/${var.environment}/${var.application_name}/AUTH_COGNITO_ISSUER"
          name      = "AUTH_COGNITO_ISSUER"
        },
        #UI parameter Astro Auth (Auth.js)
        {
          valueFrom = "/${var.environment}/${var.application_name}/AUTH_SECRET"
          name      = "AUTH_SECRET"
        }
      ]

    }
  ])
}


# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${var.application_name}-${var.environment}"
  retention_in_days = 30
}

# app ECS Service
resource "aws_ecs_service" "app_service" {
  name            = "${var.application_name}-${var.environment}-service"
  cluster         = aws_ecs_cluster.app_cluster.id
  task_definition = aws_ecs_task_definition.app_task.arn
  desired_count   = 2
  launch_type     = "FARGATE"


  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    container_name   = "agentic-workflow-accelerator-ui-${var.environment}"
    container_port   = 8000
  }

  # Allow external changes without Terraform plan difference
  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener.app_listener]
}


# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.application_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    self      = true
  }
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "${var.application_name}-${var.environment}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Application Load Balancer
resource "aws_lb" "app_alb" {
  name               = "${var.application_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false
}

# ALB Listener
resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }
}

resource "aws_lb_listener_rule" "app_listener_rule" {
  listener_arn = aws_lb_listener.app_listener.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# app ALB Target Group
resource "aws_lb_target_group" "ecs_tg" {
  name        = "${var.application_name}-app-${var.environment}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 15
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  slow_start = 120
}


# SSM Parameter for .env
resource "aws_ssm_parameter" "settings" {
  name  = "/${var.environment}/${var.application_name}/config"
  type  = "String"
  value = "initial-value" # Replace with current settings.  Should not include any secrets!
  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Environment = var.environment
  }
}


# ECS Task IAM Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.application_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for ECS Task Role
resource "aws_iam_role_policy" "ecs_task_role_policy" {
  name = "${var.application_name}-${var.environment}-ecs-task-role-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # {
      #   Effect = "Allow"
      #   Action = [
      #     "s3:*"
      #   ]
      #   Resource = [
      #     aws_s3_bucket.artifacts.arn,
      #     "${aws_s3_bucket.artifacts.arn}/*"
      #   ]
      # },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.region}:${var.aws_account_id}:parameter/${var.environment}/${var.application_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = aws_kms_key.ssm_parameters.arn
      }
    ]
  })
}

variable "ssm_secret_names" {
  type = list(string)
  default = [
    "AUTH_COGNITO_CLIENT_ID",
    "AUTH_COGNITO_CLIENT_SECRET",
    "AUTH_COGNITO_ISSUER",
    "AUTH_SECRET"
    # Add more variable names as needed
  ]
}

# SSM Parameter for .env
resource "aws_ssm_parameter" "app_secrets" {
  for_each = toset(var.ssm_secret_names)

  name      = "/${var.environment}/${var.application_name}/${each.key}"
  type      = "SecureString"
  data_type = "text"
  key_id    = aws_kms_key.ssm_parameters.id
  value     = "default-value" # Use a default value for all
  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Environment = var.environment
    Application = var.application_name
    Name        = each.key
  }
}

# Outputs
output "ecr_api_repository_url" {
  description = "The URL of the AWA API ECR repository"
  value       = aws_ecr_repository.api_repo.repository_url
}
output "ecr_ui_repository_url" {
  description = "The URL of the AWA UI ECR repository"
  value       = aws_ecr_repository.ui_repo.repository_url
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.app_cluster.name
}

output "load_balancer_dns" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.app_alb.dns_name
}
