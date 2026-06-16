# CI/CD Workflows

AWA provides robust support for running workflows in CI/CD environments through a containerized pipeline runner. This enables consistent, reproducible execution of agentic workflows across different platforms including GitHub Actions, GitLab CI, Jenkins, and more.

## Overview

The AWA Workflow Runner uses [Dagger](https://dagger.io/) to create a containerized execution environment that eliminates environment-specific issues and provides consistent results whether running locally or in production CI/CD systems.

### Key Benefits

- **Consistent Environment** - Same execution environment locally and in CI/CD
- **Cross-Platform Support** - Works with any CI platform that supports Docker containers
- **Secure Authentication** - Built-in support for AWS OIDC and CodeArtifact integration
- **Fast Feedback** - Test complete pipelines locally before pushing to remote CI
- **Comprehensive Logging** - Detailed error reporting and troubleshooting capabilities

## Architecture

The pipeline runner provides a complete AWA execution environment with:

- **Python 3.12** base container with all dependencies
- **Temporal server and worker** for workflow orchestration
- **AWS CLI and CodeArtifact** integration for private packages
- **Node.js and PNPM** for cookbook recipes
- **Automatic service startup** and health checks

## Complete Implementation Guide

For comprehensive setup instructions, complete code examples, authentication setup, configuration options, and troubleshooting guide, see the detailed cookbook recipe for the **GitHub PR Description**.

### Working Example

See the [AWA Helper Repository](https://github.com/slalombuild/agentic-workflow-accelerator-helper) for a complete working implementation of AWA workflows running in GitHub Actions, including the pipeline runner and workflow configurations used in production.

The cookbook recipe includes everything you need:

- **Complete pipeline runner implementation** with full source code
- **Step-by-step setup instructions** for GitHub Actions and local development
- **AWS OIDC authentication configuration** for secure cloud deployments
- **Environment variable setup** and credential management
- **Error handling and debugging** strategies with comprehensive logging
- **Performance optimization** techniques and best practices
- **Cross-platform deployment** examples for different CI systems
- **Local development workflows** for faster iteration and testing

The containerized approach ensures your agentic workflows run consistently across all environments while providing the flexibility needed for both development and production use cases.
