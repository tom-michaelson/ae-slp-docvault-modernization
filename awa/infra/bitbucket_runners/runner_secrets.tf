
# AWS Secrets Manager Secrets for Runner Credentials
# Shared credentials (same for all runners)
resource "aws_secretsmanager_secret" "bitbucket_shared_credentials" {
  name                    = "bitbucket-shared-credentials"
  description             = "Shared Bitbucket credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "bitbucket-shared-credentials"
    Purpose = "bitbucket-runner-authentication"
  }
}

resource "aws_secretsmanager_secret_version" "bitbucket_shared_credentials" {
  secret_id = aws_secretsmanager_secret.bitbucket_shared_credentials.id
  secret_string = jsonencode({
    account_uuid    = "PLACEHOLDER_ACCOUNT_UUID"
    repository_uuid = "PLACEHOLDER_REPOSITORY_UUID"
  })
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Individual runner credentials (key-value pairs within single secret per runner)
resource "aws_secretsmanager_secret" "bitbucket_runner_1" {
  name                    = "bitbucket-runner-1"
  description             = "Bitbucket runner 1 credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "bitbucket-runner-1"
    Purpose = "bitbucket-runner-authentication"
  }
}

resource "aws_secretsmanager_secret_version" "bitbucket_runner_1" {
  secret_id = aws_secretsmanager_secret.bitbucket_runner_1.id
  secret_string = jsonencode({
    runner_uuid         = "PLACEHOLDER_RUNNER_1_UUID"
    oauth_client_id     = "PLACEHOLDER_OAUTH_CLIENT_ID_1"
    oauth_client_secret = "PLACEHOLDER_OAUTH_CLIENT_SECRET_1"
  })
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "bitbucket_runner_2" {
  name                    = "bitbucket-runner-2"
  description             = "Bitbucket runner 2 credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "bitbucket-runner-2"
    Purpose = "bitbucket-runner-authentication"
  }
}

resource "aws_secretsmanager_secret_version" "bitbucket_runner_2" {
  secret_id = aws_secretsmanager_secret.bitbucket_runner_2.id
  secret_string = jsonencode({
    runner_uuid         = "PLACEHOLDER_RUNNER_2_UUID"
    oauth_client_id     = "PLACEHOLDER_OAUTH_CLIENT_ID_2"
    oauth_client_secret = "PLACEHOLDER_OAUTH_CLIENT_SECRET_2"
  })
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "bitbucket_runner_3" {
  name                    = "bitbucket-runner-3"
  description             = "Bitbucket runner 3 credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "bitbucket-runner-3"
    Purpose = "bitbucket-runner-authentication"
  }
}

resource "aws_secretsmanager_secret_version" "bitbucket_runner_3" {
  secret_id = aws_secretsmanager_secret.bitbucket_runner_3.id
  secret_string = jsonencode({
    runner_uuid         = "PLACEHOLDER_RUNNER_3_UUID"
    oauth_client_id     = "PLACEHOLDER_OAUTH_CLIENT_ID_3"
    oauth_client_secret = "PLACEHOLDER_OAUTH_CLIENT_SECRET_3"
  })
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "bitbucket_runner_4" {
  name                    = "bitbucket-runner-4"
  description             = "Bitbucket runner 4 credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "bitbucket-runner-4"
    Purpose = "bitbucket-runner-authentication"
  }
}

resource "aws_secretsmanager_secret_version" "bitbucket_runner_4" {
  secret_id = aws_secretsmanager_secret.bitbucket_runner_4.id
  secret_string = jsonencode({
    runner_uuid         = "PLACEHOLDER_RUNNER_4_UUID"
    oauth_client_id     = "PLACEHOLDER_OAUTH_CLIENT_ID_4"
    oauth_client_secret = "PLACEHOLDER_OAUTH_CLIENT_SECRET_4"
  })
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "bitbucket_runner_5" {
  name                    = "bitbucket-runner-5"
  description             = "Bitbucket runner 5 credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "bitbucket-runner-5"
    Purpose = "bitbucket-runner-authentication"
  }
}

resource "aws_secretsmanager_secret_version" "bitbucket_runner_5" {
  secret_id = aws_secretsmanager_secret.bitbucket_runner_5.id
  secret_string = jsonencode({
    runner_uuid         = "PLACEHOLDER_RUNNER_5_UUID"
    oauth_client_id     = "PLACEHOLDER_OAUTH_CLIENT_ID_5"
    oauth_client_secret = "PLACEHOLDER_OAUTH_CLIENT_SECRET_5"
  })
  lifecycle {
    ignore_changes = [secret_string]
  }
}
