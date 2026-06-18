#!/bin/bash

# Set error handling
set -e

# Log everything
exec > >(tee /var/log/user-data.log) 2>&1

echo "Starting user-data script execution at $(date)"

# Update system
yum update -y

# Install required dependencies
yum install -y docker git awscli jq amazon-ssm-agent cronie
sudo yum install -y java-11-amazon-corretto-headless

# Install build dependencies for Python 3.12 with SSL support
yum groupinstall "Development Tools" -y
yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget xz-devel readline-devel sqlite-devel

# Start and enable services
systemctl start crond
systemctl enable crond

# Install Dagger CLI
echo "Installing Dagger CLI..."
cd /tmp
curl -L https://dl.dagger.io/dagger/install.sh | sh
mv bin/dagger /usr/local/bin/
chmod +x /usr/local/bin/dagger
# Create dedicated pipeline user
useradd -m -s /bin/bash pipeline-user || echo "User pipeline-user already exists"
usermod -aG docker pipeline-user
usermod -aG wheel pipeline-user

# Enable passwordless sudo for pipeline-user
echo "pipeline-user ALL=(ALL) NOPASSWD: /bin/systemctl start docker, /bin/systemctl stop docker, /bin/systemctl restart docker" >> /etc/sudoers.d/pipeline-user

# Ensure Docker starts on boot and pipeline-user has access
systemctl enable docker
systemctl start docker
chown root:docker /var/run/docker.sock
chmod 660 /var/run/docker.sock

# Install uv as pipeline-user
echo "Installing uv..."
sudo -u pipeline-user bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'

# Set up environment for pipeline-user
sudo -u pipeline-user bash -c 'echo "export PATH=\$HOME/.local/bin:\$PATH" >> ~/.bashrc'

# Install Python 3.12
echo "Installing Python 3.12..."
sudo -u pipeline-user bash -c 'export PATH=$HOME/.local/bin:$PATH && uv python install 3.12'

# Verify Python installation
echo "Verifying Python installation..."
sudo -u pipeline-user bash -c 'python3 --version'

# Set up Dagger configuration
sudo -u pipeline-user mkdir -p /home/pipeline-user/.config/dagger
sudo -u pipeline-user touch /home/pipeline-user/.config/dagger/engine.json
sudo -u pipeline-user bash -c 'cat > /home/pipeline-user/.config/dagger/engine.json << "EOF"
{
  "gc": {
    "maxUsedSpace": "200GB",
    "reservedSpace": "10GB",
    "minFreeSpace": "20%",
    "sweepSize": "50%"
  }
}
EOF'

# Install Docker Compose
sudo -u pipeline-user mkdir -p /home/pipeline-user/.docker/cli-plugins
sudo -u pipeline-user bash -c 'curl -SL https://github.com/docker/compose/releases/download/v2.39.1/docker-compose-linux-x86_64 -o /home/pipeline-user/.docker/cli-plugins/docker-compose'
sudo -u pipeline-user bash -c 'chmod +x /home/pipeline-user/.docker/cli-plugins/docker-compose'

# Start SSM agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Create runner directory
mkdir -p /home/pipeline-user/bitbucket-runner
chown pipeline-user:pipeline-user /home/pipeline-user/bitbucket-runner

# Download and install official Bitbucket runner
cd /home/pipeline-user/bitbucket-runner
sudo -u pipeline-user bash -c 'curl https://product-downloads.atlassian.com/software/bitbucket/pipelines/atlassian-bitbucket-pipelines-runner.tar.gz --output atlassian-bitbucket-pipelines-runner.tar.gz'

# Extract the runner
sudo -u pipeline-user bash -c 'mkdir atlassian-bitbucket-pipelines-runner && tar -xzvf atlassian-bitbucket-pipelines-runner.tar.gz -C atlassian-bitbucket-pipelines-runner'

# Get instance ID for unique identification with error handling
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id || echo "unknown")
if [ "$INSTANCE_ID" = "unknown" ] || [ -z "$INSTANCE_ID" ]; then
    echo "WARNING: Could not retrieve instance ID, using fallback"
    INSTANCE_ID="fallback-$(date +%s)"
fi

RUNNER_ID="runner-$(echo $INSTANCE_ID | cut -c1-8)"
RUNNER_NAME="ec2-runner-$(hostname)-${RUNNER_ID}"

# Get token index based on last 1 digit of instance ID
LAST_DIGIT=$(echo $INSTANCE_ID | grep -o '[0-9]$')
if [ -n "$LAST_DIGIT" ]; then
    TOKEN_INDEX=$(( (${LAST_DIGIT} % 5) + 1 ))
else
    # Fallback if no digits found
    TOKEN_INDEX=1
fi

echo "Instance ID: ${INSTANCE_ID}"
echo "Using runner credentials set: ${TOKEN_INDEX}"

# Retrieve shared credentials (same for all runners)
SHARED_CREDS=$(aws secretsmanager get-secret-value \
  --secret-id "bitbucket-shared-credentials" \
  --query "SecretString" \
  --output text)

ACCOUNT_UUID=$(echo $SHARED_CREDS | jq -r '.account_uuid')
REPOSITORY_UUID=$(echo $SHARED_CREDS | jq -r '.repository_uuid')

# Retrieve individual runner credentials based on TOKEN_INDEX
RUNNER_CREDS=$(aws secretsmanager get-secret-value \
  --secret-id "bitbucket-runner-${TOKEN_INDEX}" \
  --query "SecretString" \
  --output text)

RUNNER_UUID=$(echo $RUNNER_CREDS | jq -r '.runner_uuid')
OAUTH_CLIENT_ID=$(echo $RUNNER_CREDS | jq -r '.oauth_client_id')
OAUTH_CLIENT_SECRET=$(echo $RUNNER_CREDS | jq -r '.oauth_client_secret')

# Validate that all credentials were retrieved successfully
if [ -z "$ACCOUNT_UUID" ] || [ -z "$REPOSITORY_UUID" ] || [ -z "$RUNNER_UUID" ] || [ -z "$OAUTH_CLIENT_ID" ] || [ -z "$OAUTH_CLIENT_SECRET" ]; then
    echo "ERROR: Failed to retrieve one or more credentials from Secrets Manager"
    echo "Account UUID: ${ACCOUNT_UUID:-MISSING}"
    echo "Repository UUID: ${REPOSITORY_UUID:-MISSING}"
    echo "Runner UUID: ${RUNNER_UUID:-MISSING}"
    echo "OAuth Client ID: ${OAUTH_CLIENT_ID:-MISSING}"
    echo "OAuth Client Secret: ${OAUTH_CLIENT_SECRET:-MISSING}"
    exit 1
fi

echo "Successfully retrieved credentials for runner ${TOKEN_INDEX}"

# Create working directory
sudo -u pipeline-user mkdir -p /home/pipeline-user/bitbucket-runner/temp

# Create runner configuration script with correct UUID format (including curly braces)
sudo -u pipeline-user bash -c 'cat > /home/pipeline-user/bitbucket-runner/start-runner.sh << "EOF"
#!/bin/bash
cd /home/pipeline-user/bitbucket-runner/atlassian-bitbucket-pipelines-runner/bin

# Get credentials from Secrets Manager
SHARED_CREDS=$(aws secretsmanager get-secret-value --secret-id "bitbucket-shared-credentials" --query "SecretString" --output text)
ACCOUNT_UUID=$(echo $SHARED_CREDS | jq -r ".account_uuid")
REPOSITORY_UUID=$(echo $SHARED_CREDS | jq -r ".repository_uuid")

# Get TOKEN_INDEX from environment variable
if [ -z "$TOKEN_INDEX" ]; then
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id || echo "unknown")
    if [ "$INSTANCE_ID" != "unknown" ] && [ -n "$INSTANCE_ID" ]; then
        FIRST_CHAR=$(echo $INSTANCE_ID | cut -c1-1)
        if [[ "$FIRST_CHAR" =~ [0-9a-f] ]]; then
            TOKEN_INDEX=$(( $(echo $FIRST_CHAR | tr "a-f" "1-6" | tr "0-9" "1-9") % 5 + 1 ))
        else
            TOKEN_INDEX=1
        fi
    else
        TOKEN_INDEX=1
    fi
fi

# Get runner-specific credentials
RUNNER_CREDS=$(aws secretsmanager get-secret-value --secret-id "bitbucket-runner-${TOKEN_INDEX}" --query "SecretString" --output text)
RUNNER_UUID=$(echo $RUNNER_CREDS | jq -r ".runner_uuid")
OAUTH_CLIENT_ID=$(echo $RUNNER_CREDS | jq -r ".oauth_client_id")
OAUTH_CLIENT_SECRET=$(echo $RUNNER_CREDS | jq -r ".oauth_client_secret")

# Check if credentials are valid
if [ "$ACCOUNT_UUID" = "PLACEHOLDER" ] || [ "$REPOSITORY_UUID" = "PLACEHOLDER" ] || [ "$RUNNER_UUID" = "PLACEHOLDER" ]; then
    echo "ERROR: Credentials not properly configured. Please update the secrets in AWS Secrets Manager."
    echo "Account UUID: $ACCOUNT_UUID"
    echo "Repository UUID: $REPOSITORY_UUID"
    echo "Runner UUID: $RUNNER_UUID"
    exit 1
fi

echo "Starting Bitbucket runner with credentials..."
echo "Account UUID: {$ACCOUNT_UUID}"
echo "Repository UUID: {$REPOSITORY_UUID}"
echo "Runner UUID: {$RUNNER_UUID}"

# Start the runner with correct UUID format (including curly braces) - all on one line
./start.sh --accountUuid {$ACCOUNT_UUID} --repositoryUuid {$REPOSITORY_UUID} --runnerUuid {$RUNNER_UUID} --OAuthClientId $OAUTH_CLIENT_ID --OAuthClientSecret $OAUTH_CLIENT_SECRET --runtime linux-shell --workingDirectory /home/pipeline-user/bitbucket-runner/temp
EOF'

sudo -u pipeline-user chmod +x /home/pipeline-user/bitbucket-runner/start-runner.sh

# Create systemd service
cat > /etc/systemd/system/bitbucket-runner.service << EOF
[Unit]
Description=Bitbucket Self-Hosted Runner (${RUNNER_NAME})
After=network.target

[Service]
Type=simple
User=pipeline-user
Group=pipeline-user
WorkingDirectory=/home/pipeline-user/bitbucket-runner
ExecStart=/home/pipeline-user/bitbucket-runner/start-runner.sh
Restart=always
RestartSec=10
Environment=RUNNER_ID=${RUNNER_ID}
Environment=RUNNER_NAME=${RUNNER_NAME}
Environment=TOKEN_INDEX=${TOKEN_INDEX}

[Install]
WantedBy=multi-user.target
EOF

# Create shutdown script for graceful termination
sudo -u pipeline-user bash -c 'cat > /home/pipeline-user/bitbucket-runner/shutdown.sh << "EOF"
#!/bin/bash
# Graceful shutdown script
echo "Shutting down Bitbucket runner ${RUNNER_NAME}..."

# Stop the runner service
systemctl stop bitbucket-runner

# Wait for any running jobs to complete (with timeout)
timeout 300 bash -c "while systemctl is-active --quiet bitbucket-runner; do sleep 5; done"

# Notify ASG that instance is ready for termination
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws autoscaling complete-lifecycle-action \\
  --lifecycle-hook-name bitbucket-runner-shutdown-dev \\
  --auto-scaling-group-name bitbucket-runner-dev-asg \\
  --lifecycle-action-result CONTINUE \\
  --instance-id $INSTANCE_ID \\
  --region us-east-1

echo "Runner ${RUNNER_NAME} shutdown complete"
EOF'

sudo -u pipeline-user chmod +x /home/pipeline-user/bitbucket-runner/shutdown.sh

# Enable and start the service
systemctl daemon-reload
systemctl enable bitbucket-runner
systemctl start bitbucket-runner

# Log the registration
echo "Bitbucket runner ${RUNNER_NAME} (ID: ${RUNNER_ID}, Token Index: ${TOKEN_INDEX}) registration initiated at $(date)" >> /var/log/bitbucket-runner.log

# Create a status check script for monitoring
sudo -u pipeline-user bash -c 'cat > /home/pipeline-user/bitbucket-runner/status-check.sh << "EOF"
#!/bin/bash
# Status check script for monitoring

RUNNER_NAME=${RUNNER_NAME}
TOKEN_INDEX=${TOKEN_INDEX}

echo "=== Bitbucket Runner Status ==="
echo "Runner Name: ${RUNNER_NAME}"
echo "Token Index: ${TOKEN_INDEX}"
echo "Service Status: $(systemctl is-active bitbucket-runner)"
echo "Service State: $(systemctl is-enabled bitbucket-runner)"
echo "Last Updated: $(date)"

# Check if the runner process is running
if pgrep -f "start.sh" > /dev/null; then
    echo "Runner Process: RUNNING"
else
    echo "Runner Process: NOT RUNNING"
fi

# Check recent logs
echo "=== Recent Logs ==="
journalctl -u bitbucket-runner --since "5 minutes ago" --no-pager | tail -10
EOF'

sudo -u pipeline-user chmod +x /home/pipeline-user/bitbucket-runner/status-check.sh

# Create a cron job to run status check every 5 minutes
echo "*/5 * * * * /home/pipeline-user/bitbucket-runner/status-check.sh >> /var/log/bitbucket-runner-status.log 2>&1" | crontab -u pipeline-user -

echo "Bitbucket runner setup completed successfully!"
echo "Runner Name: ${RUNNER_NAME}"
echo "Token Index: ${TOKEN_INDEX}"
echo "Account UUID: ${ACCOUNT_UUID}"
echo "Repository UUID: ${REPOSITORY_UUID}"
echo "Runner UUID: ${RUNNER_UUID}"

echo "User-data script completed at $(date)"
