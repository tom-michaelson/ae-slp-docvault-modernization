# Terraform backend configuration for S3
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "awa-infra-tfstate"
    key    = "awa-infra.tfstate"
    region = "us-east-1"
  }
}

# Define the provider
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = var.environment
      Application = "AWA"
      ManagedBy   = "Terraform"
    }
  }
}
