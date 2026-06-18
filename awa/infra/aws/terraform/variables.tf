# Generic Variables
variable "region" {
  description = "The AWS region where resources will be created."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "The AWS account ID."
  type        = string
}

variable "environment" {
  description = "The environment this terraform applies to."
  type        = string
  default     = "dev"
}

variable "application_name" {
  type        = string
  description = "The name of the application"
}

variable "domain" {
  description = "The base domain name for the application"
  default     = "awa.slalomdev.io"
}

# Networking Variables
variable "vpc_id" {
  type        = string
  description = "The VPC ID where resources will be deployed"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for the Fargate service"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "List of public subnet IDs for the load balancer"
}
