# Deployment

## Manual Docker Build

### UI

Follow these steps to manually build and push the Docker image to ECR.

1. Build the Docker image

```bash
docker buildx build --platform linux/amd64 -f Dockerfile.ui -t agentic-workflow-accelerator-ui-prod:latest .
```

2. Tag the Docker image

```bash
docker tag agentic-workflow-accelerator-ui-prod:latest 577638363028.dkr.ecr.us-east-1.amazonaws.com/agentic-workflow-accelerator-ui-prod:latest
```

3. Login to ECR

Replace `<aws profile name>` with the name of the AWS profile you want to use (or remove the `--profile` flag if you are using the default profile).

```bash
aws ecr get-login-password --region us-east-1 --profile <aws profile name> | docker login --username AWS --password-stdin 577638363028.dkr.ecr.us-east-1.amazonaws.com
```

4. Push the Docker image to ECR

```bash
docker push 577638363028.dkr.ecr.us-east-1.amazonaws.com/agentic-workflow-accelerator-ui-prod:latest
```
