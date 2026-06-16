#this is a stub! no vars have been checked for accuracy
#Account id is 509399639490
region            = "us-east-1"
environment       = "infra"
aws_account_id    = "509399639490"
application_name  = "awa"
domain            = "awa.slalomdev.io"
ssm_parameter_key = "arn:aws:kms:us-east-1:577638363028:key/7c0d4aeb-8c90-4d63-a05e-f7ae3e16455d"
# vpc_cidr              = "10.0.0.0/16"
# public_subnet_1_cidr  = "10.0.1.0/24"
# public_subnet_2_cidr  = "10.0.2.0/24"
# private_subnet_1_cidr = "10.0.3.0/24"
# private_subnet_2_cidr = "10.0.4.0/24"
vpc_id             = "vpc-08a2aa7f46305ff1c"
private_subnet_ids = ["subnet-0febb81f62a1adbe6", "subnet-046f7287c47d0b0e6"]
public_subnet_ids  = ["subnet-0899b46b8f36ff203", "subnet-0a0f3605f279e0b88"]
