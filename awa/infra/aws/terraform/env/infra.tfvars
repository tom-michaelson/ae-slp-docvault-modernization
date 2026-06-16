#this is a stub! no vars have been checked for accuracy
#this is meant to deploy into a separate namespace for testing TF changes.
region            = "us-east-1"
environment       = "TFTest"
aws_account_id    = "577638363028"
application_name  = "awa"
domain            = "infra.slalomdev.io"
vpc_id             = "vpc-08a2aa7f46305ff1c"
private_subnet_ids = ["subnet-0febb81f62a1adbe6", "subnet-046f7287c47d0b0e6"]
public_subnet_ids  = ["subnet-0899b46b8f36ff203", "subnet-0a0f3605f279e0b88"]
