# Environment Configuration

This is a reference for environment variables. You can use a root `.env` file to set these variables.

Copy the `.env.example` file as a starting point.

## System

| Variable              | Type     | Required             | Default            | Note                                                                                                                      |
| --------------------- | -------- | -------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `DEBUG_MODE`          | `bool`   | No                   | `false`            | Whether to run the Temporal worker in debug mode. Must set to `true` in order for Python debugger to work properly.       |
| `HOME_DIR`            | `string` | Yes, if using Docker |                    | Home directory for the current user. Only used when running with Docker.                                                  |
| `PYTHONPYCACHEPREFIX` | `string` | No                   | `./.cache/pycache` | Sets the Python cache directory. Useful to set to avoid `__pycache__` directories being created in each module directory. |

## Auth

| Variable                     | Type     | Required             | Default          | Note                                                                                       |
| ---------------------------- | -------- | -------------------- | ---------------- | ------------------------------------------------------------------------------------------ |
| `PUBLIC_AUTH_MODE`           | `enum`   | No                   | `none`           | Authentication mode. Options: `none` (no auth) or `cognito` (OAuth with Cognito).          |
| `AUTH_COGNITO_CLIENT_ID`     | `string` | If mode is `cognito` |                  | Cognito client ID.                                                                         |
| `AUTH_COGNITO_CLIENT_SECRET` | `string` | If mode is `cognito` |                  | Cognito client secret.                                                                     |
| `AUTH_COGNITO_ISSUER`        | `string` | If mode is `cognito` |                  | Cognito issuer. Example: `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_frVRXFrzw` |
| `AUTH_SECRET`                | `string` | No                   | `default_secret` | Auth.js secret value.                                                                      |

## LLM Providers

| Variable                 | Type     | Required | Default | Note                            |
| ------------------------ | -------- | -------- | ------- | ------------------------------- |
| `LITE_LLM_API_KEY`       | `string` | No       |         | API key for the Lite LLM proxy. |
| `AZURE_OPENAI_API_KEY`   | `string` | No       |         | API key for Azure OpenAI.       |
| `OPENAI_API_KEY`         | `string` | No       |         | API key for OpenAI.             |
| `GITHUB_COPILOT_API_KEY` | `string` | No       |         | API key for Github Copilot.     |

## Langfuse

| Variable              | Type     | Required | Default          | Note                 |
| --------------------- | -------- | -------- | ---------------- | -------------------- |
| `LANGFUSE_SECRET_KEY` | `string` | No       | `the_secret_key` | Langfuse secret key. |
| `LANGFUSE_PUBLIC_KEY` | `string` | No       | `the_public_key` | Langfuse public key. |

## External Services

| Variable       | Type     | Required | Default | Note              |
| -------------- | -------- | -------- | ------- | ----------------- |
| `JIRA_API_KEY` | `string` | No       |         | API key for Jira. |

## AWS

These environment variables are used when accessing AWS resources, including Bedrock and S3.

| Variable                | Type     | Required | Default | Note                   |
| ----------------------- | -------- | -------- | ------- | ---------------------- |
| `AWS_REGION`            | `string` | No       |         | AWS region.            |
| `AWS_PROFILE`           | `string` | No       |         | AWS profile.           |
| `AWS_ACCESS_KEY_ID`     | `string` | No       |         | AWS access key ID.     |
| `AWS_SECRET_ACCESS_KEY` | `string` | No       |         | AWS secret access key. |

## Logging

| Variable                 | Type     | Required | Default | Note                                        |
| ------------------------ | -------- | -------- | ------- | ------------------------------------------- |
| `LOG_LEVEL`              | `string` | No       | `INFO`  | Log level.                                  |
| `LOG_DIR`                | `string` | No       | `logs`  | Log directory for application logs.         |
| `LOG_WORKFLOW_DIR`       | `string` | No       | `logs`  | Log directory for workflow logs.            |
| `LOG_FILE_ROTATION_SIZE` | `string` | No       | `1 MB`  | Log file rotation size.                     |
| `LOG_CONSOLE_ENABLED`    | `bool`   | No       | `true`  | Whether to enable console logging.          |
| `LOG_FILE_ENABLED`       | `bool`   | No       | `true`  | Whether to enable file logging.             |
| `LOG_ENABLE_JSON`        | `bool`   | No       | `false` | Whether to enable structrured JSON logging. |

## Core Service Config

| Variable                      | Type     | Required | Default                        | Note                                                                                   |
| ----------------------------- | -------- | -------- | ------------------------------ | -------------------------------------------------------------------------------------- |
| `AWA_UI_HOST`                 | `string` | No       | `localhost`                    | Host for the AWA UI server.                                                            |
| `AWA_UI_PORT`                 | `int`    | No       | `8000`                         | Port for the AWA UI server.                                                            |
| `AWA_API_HOST`                | `string` | No       | `localhost`                    | Host for the AWA API server.                                                           |
| `AWA_API_PORT`                | `int`    | No       | `8001`                         | Port for the AWA API server.                                                           |
| `TEMPORAL_UI_HOST`            | `string` | No       | `localhost`                    | Host for the Temporal UI server.                                                       |
| `TEMPORAL_UI_PORT`            | `int`    | No       | `8002`                         | Port for the Temporal UI server.                                                       |
| `TEMPORAL_SERVER_HOST`        | `string` | No       | `localhost`                    | Host for the Temporal server.                                                          |
| `TEMPORAL_SERVER_PORT`        | `int`    | No       | `7233`                         | Port for the Temporal server.                                                          |
| `TEMPORAL_METRICS_PORT`       | `int`    | No       | `8004`                         | Port for the Temporal metrics server.                                                  |
| `TEMPORAL_VERSION`            | `string` | No       | `2.34.0`                       | Version of Temporal to use. Only used when running with Docker.                        |
| `TEMPORAL_ADMINTOOLS_VERSION` | `string` | No       | `1.27.2-tctl-1.18.2-cli-1.3.0` | Version of Temporal Admin Tools to use. Only used when running with Docker.            |
| `TEMPORAL_UI_VERSION`         | `string` | No       | `1.27.2`                       | Version of Temporal UI to use. Only used when running with Docker.                     |
| `POSTGRESQL_VERSION`          | `string` | No       | `16`                           | Version of PostgreSQL to use for Temporal. Only used when running with Docker.         |
| `POSTGRES_PASSWORD`           | `string` | No       | `temporal`                     | Password for the Temporal PostgreSQL database. Only used when running with Docker.     |
| `POSTGRES_USER`               | `string` | No       | `temporal`                     | User for the Temporal PostgreSQL database. Only used when running with Docker.         |
| `POSTGRES_DEFAULT_PORT`       | `int`    | No       | `5432`                         | Default port for the Temporal PostgreSQL database. Only used when running with Docker. |
