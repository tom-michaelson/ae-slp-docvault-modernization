resource "aws_kms_key" "ssm_parameters" {
  description             = "KMS key for encrypting SSM parameters used by ECS tasks"
  enable_key_rotation     = true
  deletion_window_in_days = 10
  key_usage               = "ENCRYPT_DECRYPT"
  is_enabled              = true

}

resource "aws_kms_alias" "ssm_parameters" {
  name          = "alias/${var.application_name}-${var.environment}-ssm-parameters"
  target_key_id = aws_kms_key.ssm_parameters.key_id
}

# Example: Allow an ECS task role to decrypt SSM parameters
# Replace var.ecs_task_role_arn with your ECS task role ARN variable
resource "aws_kms_key_policy" "ssm_parameters" {
  key_id = aws_kms_key.ssm_parameters.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "ssm-key-policy"
    Statement = [
      {
        Sid       = "Enable IAM User Permissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${var.aws_account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "Allow ECS Task Role to use the key for decryption"
        Effect    = "Allow"
        Principal = { AWS = [aws_iam_role.ecs_task_role.arn, aws_iam_role.ecs_task_execution_role.arn] }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        "Sid" : "Allow access through SSM for all principals in the account that are authorized to use SSM",
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "*"
        },
        "Action" : [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ],
        "Resource" : "*",
        "Condition" : {
          "StringEquals" : {
            "kms:ViaService" : "ssm.us-east-1.amazonaws.com",
            "kms:CallerAccount" : "${var.aws_account_id}"
          }
        }
      }
    ]
  })
}

# data "aws_caller_identity" "current" {}
