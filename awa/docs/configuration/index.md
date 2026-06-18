# Configuration

AWA is configured in two ways: environment (.env) and application (config.yaml).

## Environment (.env)

AWA looks for a `.env` file in the root of its directory. This file contains secret values and other configuration values.

You don't have to use this file, though. You can instead set environment variables in your operating system.

For a full reference of all supported environment variables, see [Reference - Configuration - .env](/reference/configuration/environment).

## Application (config.yaml)

Non-secret configuration values are stored in `config.yaml`, by default in the root of AWA's directory.

For a full reference of all supported application configuration variables, see [Reference - Configuration - config.yaml](/reference/configuration/application).

## Recipes

AWA includes a collection of example workflows and tutorials (recipes) that can be enabled through configuration. To enable recipes, set `recipes: true` in your `config.yaml` file.

For detailed information about recipe configuration, see [Recipe Configuration](/cookbook/configuration).

## Authentication

AWA supports OAuth authentication with AWS Cognito SSO to secure API endpoints. See [Authentication Configuration](/configuration/authentication) for setup instructions.
