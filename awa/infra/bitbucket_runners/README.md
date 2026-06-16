# Automated Bitbucket Self-Hosted Runners

This document describes the automated deployment of Bitbucket self-hosted runners using AWS Auto Scaling Groups (ASG) with scheduled scaling and automatic runner registration.

## Overview

The AWA project uses an automated infrastructure approach for Bitbucket self-hosted runners that eliminates manual setup steps. The system includes:

- **Auto Scaling Groups (ASG)** for dynamic instance management
- **Scheduled scaling** for cost optimization
- **Automatic runner registration** using AWS Secrets Manager
- **Unique runner assignment** to prevent conflicts
- **Graceful shutdown** handling

## Architecture

### Components

1. **Auto Scaling Group (ASG)**
   - Manages EC2 instances automatically
   - Scales between 0-5 instances based on demand
   - Uses launch templates for consistent configuration

2. **Scheduled Scaling**
   - **Scale Up**: 7:00 AM CST (12:00 PM UTC) - Sets desired capacity to 2
   - **Scale Down**: 7:00 PM CST (12:00 AM UTC) - Sets desired capacity to 0
   - Optimizes costs by running only during business hours

3. **Secrets Management**
   - **Shared credentials**: Account UUID and Repository UUID (same for all runners)
   - **Individual runner credentials**: 5 sets of runner-specific tokens
   - Stored in AWS Secrets Manager with JSON key-value structure

4. **Instance Configuration**
   - **AMI**: Amazon Linux 2023.8 (us-east-1)
   - **Instance Type**: t3.large
   - **Storage**: 200GB GP3 EBS volume
   - **Security Groups**: HTTPS outbound access for Bitbucket API

## Automated Setup Process

### 1. Infrastructure Deployment

The infrastructure is deployed using Terraform:

```bash
cd infra/bitbucket_runners
terraform init
terraform plan --var-file=env/prod.tfvars
terraform apply --var-file=env/prod.tfvars
```

### 2. Secrets Configuration

Before deployment, configure the required secrets in AWS Secrets Manager:

#### Shared Credentials
```json
{
  "account_uuid": "your-bitbucket-account-uuid",
  "repository_uuid": "your-repository-uuid"
}
```

#### Individual Runner Credentials (5 runners)
```json
{
  "runner_uuid": "runner-uuid-1",
  "oauth_client_id": "oauth-client-id-1",
  "oauth_client_secret": "oauth-client-secret-1"
}
```

### 3. Automatic Runner Registration

When instances launch, the user data script automatically:

1. **Retrieves credentials** from AWS Secrets Manager
2. **Calculates unique runner assignment** based on instance ID
3. **Installs required dependencies** (Java, Docker, Dagger, Python, etc.)
4. **Registers the runner** with Bitbucket using the assigned credentials
5. **Starts the runner service** as a systemd service
6. **Sets up monitoring** with cron-based health checks

## Scheduling Configuration

### Scale Up Schedule
- **Time**: 7:00 AM CST (12:00 PM UTC)
- **Action**: Sets desired capacity to 2 instances
- **Purpose**: Ensures runners are available for morning development work

### Scale Down Schedule
- **Time**: 7:00 PM CST (12:00 AM UTC)
- **Action**: Sets desired capacity to 0 instances
- **Purpose**: Shuts down runners outside business hours to save costs

### Manual Scaling
You can manually adjust the desired capacity:
- **Increase**: For high-demand periods
- **Decrease**: For cost optimization
- **Set to 0**: For maintenance or troubleshooting

## Runner Assignment Logic

To prevent multiple instances from using the same runner credentials, the system uses a deterministic assignment based on the instance ID:

```bash
# Get last digit of instance ID for token index (1-5)
TOKEN_INDEX=$(( $(echo $INSTANCE_ID | rev | cut -c1) % 5 + 1 ))
```

This ensures:
- Each instance gets a unique runner assignment
- Assignment is consistent across restarts
- No conflicts when multiple instances run simultaneously

## Monitoring and Health Checks

### Systemd Service
- **Service Name**: `bitbucket-runner.service`
- **User**: `pipeline-user`
- **Auto-restart**: Enabled on failure
- **Logs**: Available via `journalctl -u bitbucket-runner.service`

### Cron-based Monitoring
- **Frequency**: Every 5 minutes
- **Script**: `bitbucket_runner_monitor.sh`
- **Actions**:
  - Checks if runner is online
  - Restarts service if needed
  - Logs status to `/home/pipeline-user/bitbucket_cron_logfile.log`

## Troubleshooting

### Common Issues

1. **Runner Registration Fails**
   - Check AWS Secrets Manager permissions
   - Verify credentials are correctly formatted
   - Review `/var/log/cloud-init-output.log`

2. **Multiple Instances Using Same Runner**
   - Verify instance ID retrieval is working
   - Check token assignment logic
   - Ensure unique runner credentials in Secrets Manager
   - In case the two instance connect using the same runner credentials, terminating one instance to trigger a new instance creation is helpful.

3. **Runner Goes Offline**
   - Check systemd service status: `systemctl status bitbucket-runner.service`
   - Review cron logs: `tail -f /home/pipeline-user/bitbucket_cron_logfile.log`
   - Verify network connectivity to Bitbucket

4. **Scaling Issues**
   - Check ASG activity in AWS Console
   - Verify scheduled actions are configured
   - Review CloudWatch metrics

### Log Locations

- **User Data Script**: `/var/log/cloud-init-output.log`
- **Runner Service**: `journalctl -u bitbucket-runner.service`
- **Cron Monitoring**: `/home/pipeline-user/bitbucket_cron_logfile.log`

## Cost Optimization

### Scheduled Scaling Benefits
- **Reduced Costs**: Runners only run during business hours
- **Automatic Management**: No manual intervention required
- **Flexible Scheduling**: Easy to adjust based on team needs

### Instance Configuration
- **Right-sized Instances**: t3.large provides adequate resources
- **Efficient Storage**: GP3 EBS for better price/performance
- **Auto-termination**: Instances automatically terminate when not needed

## Security Considerations

### IAM Permissions
- **Minimal Access**: Only Secrets Manager read permissions
- **Instance Profile**: No long-term credentials stored
- **Principle of Least Privilege**: Only required AWS services accessible

### Network Security
- **HTTPS Only**: All outbound traffic uses encrypted connections
- **VPC Isolation**: Runners run in private subnets with NAT gateway access
- **Security Groups**: Restrictive outbound rules

### Secrets Management
- **Encryption**: All secrets encrypted at rest in AWS Secrets Manager
- **Rotation**: Secrets can be rotated without infrastructure changes
- **Access Control**: IAM-based access to secrets

## Maintenance

### Regular Tasks
- **Monitor Costs**: Review CloudWatch billing metrics
- **Update AMIs**: Periodically update to latest Amazon Linux versions
- **Rotate Secrets**: Update Bitbucket runner credentials as needed
- **Review Logs**: Check for any recurring issues

### Updates and Changes
- **Infrastructure Changes**: Use Terraform to modify configuration
- **User Data Updates**: Changes require instance replacement
- **Secrets Updates**: Can be done without infrastructure changes

## Support

For issues with the automated runner system:

1. **Check Logs**: Review the log locations mentioned above
2. **AWS Console**: Verify ASG and EC2 instance status
3. **Bitbucket UI**: Check runner status in repository settings
4. **Contact Team**: Reach out to the AWA development team for assistance
