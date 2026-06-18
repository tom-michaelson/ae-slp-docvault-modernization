resource "aws_iam_role" "ec2_ssm_role" {
  name               = "awa-ec2-ssm-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ssm_attach" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_ssm_profile" {
  name = "awa-ec2-ssm-profile"
  role = aws_iam_role.ec2_ssm_role.name
}


# IAM Policy for Secrets Manager access
resource "aws_iam_role_policy" "bitbucket_runner_secrets" {
  name = "bitbucket-runner-secrets-${var.environment}"
  role = aws_iam_role.ec2_ssm_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.bitbucket_shared_credentials.arn,
          aws_secretsmanager_secret.bitbucket_runner_1.arn,
          aws_secretsmanager_secret.bitbucket_runner_2.arn,
          aws_secretsmanager_secret.bitbucket_runner_3.arn,
          aws_secretsmanager_secret.bitbucket_runner_4.arn,
          aws_secretsmanager_secret.bitbucket_runner_5.arn
        ]
      }
    ]
  })
}


resource "aws_security_group" "bitbucket_runner_sg" {
  name        = "awa-bitbucket-runner-sg"
  description = "Allow outbound HTTPS for Bitbucket runner"
  vpc_id      = var.vpc_id

  egress {
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

# Launch Template
resource "aws_launch_template" "bitbucket_runner" {
  name_prefix   = "bitbucket-runner-"
  image_id      = "ami-08a6efd148b1f7504" # Amazon Linux 2023.8 AMI (us-east-1)
  instance_type = "t3.large"
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_ssm_profile.name
  }
  vpc_security_group_ids = [aws_security_group.bitbucket_runner_sg.id]
  user_data              = base64encode(file("${path.module}/scripts/user-data.sh"))
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 200
      volume_type = "gp3"
    }
  }
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "awa-bitbucket-self-hosted-runner"
    }
  }
}

# 2. Auto Scaling Group
resource "aws_autoscaling_group" "bitbucket_runner" {
  name                = "awa-bitbucket-runner-asg"
  max_size            = 2
  min_size            = 0
  desired_capacity    = 0
  vpc_zone_identifier = var.public_subnet_ids
  launch_template {
    id      = aws_launch_template.bitbucket_runner.id
    version = "$Latest"
  }
  tag {
    key                 = "Name"
    value               = "awa-bitbucket-self-hosted-runner"
    propagate_at_launch = true
  }
  # Optional: health_check_type, termination_policies, etc.
}

resource "aws_autoscaling_schedule" "scale_up_precise" {
  scheduled_action_name  = "scale-up-7-am-cst-precise"
  min_size               = 2
  max_size               = 2
  desired_capacity       = 2
  recurrence             = "0 12 * * *" # 7.00 AM CST = 12:00 PM UTC
  autoscaling_group_name = aws_autoscaling_group.bitbucket_runner.name
}

resource "aws_autoscaling_schedule" "scale_down_precise" {
  scheduled_action_name  = "scale-down-7-pm-cst-precise"
  min_size               = 0
  max_size               = 0
  desired_capacity       = 0
  recurrence             = "0 0 * * *" # 7.00 PM CST = 00.00 UTC
  autoscaling_group_name = aws_autoscaling_group.bitbucket_runner.name
}
