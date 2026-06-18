"""Init command implementation."""

import asyncio
from typing import Annotated

import typer
import yaml

from awa.core.auth import github_copilot
from awa.core.cli import constants as cli_constants
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.models.config.llm_providers_config import (
    AzureOpenAiLlmProvider,
    GithubCopilotLlmProvider,
    LiteLlmProvider,
    LlmProviderEnum,
)
from awa.core.utils.config_paths import ConfigPaths

app = typer.Typer()
init_logging()
logger = get_logger(LoggerComponent.CLI)


class LLMProviderSetup:
    """Setup logic for LLM provider configuration using existing Pydantic models."""

    def get_provider_requirements(self, provider: LlmProviderEnum) -> dict:
        """Get provider-specific setup requirements using existing models."""
        requirements = {
            LlmProviderEnum.OPEN_AI: {
                "env_vars": ["OPENAI_API_KEY"],
                "config_class": None,  # No additional config needed
                "prompts": {
                    "OPENAI_API_KEY": "OpenAI API Key",
                },
                "defaults": {},
            },
            LlmProviderEnum.AZURE_OPEN_AI: {
                "env_vars": ["AZURE_OPENAI_API_KEY"],
                "config_class": AzureOpenAiLlmProvider,
                "prompts": {
                    "AZURE_OPENAI_API_KEY": "Azure OpenAI API Key",
                    "resource_name": "Azure OpenAI Resource Name",
                    "api_version": "Azure OpenAI API Version",
                },
                "defaults": {
                    "api_version": "2024-10-21",
                },
            },
            LlmProviderEnum.AWS_BEDROCK: {
                "env_vars": ["AWS_REGION", "AWS_PROFILE"],
                "config_class": None,  # Uses AWS credentials
                "prompts": {
                    "AWS_REGION": "AWS Region",
                    "AWS_PROFILE": "AWS Profile",
                },
                "defaults": {
                    "AWS_REGION": "us-east-1",
                    "AWS_PROFILE": "default",
                },
            },
            LlmProviderEnum.LITE_LLM: {
                "env_vars": ["LITE_LLM_API_KEY"],
                "config_class": LiteLlmProvider,
                "prompts": {
                    "LITE_LLM_API_KEY": "LiteLLM API Key",
                    "base_url": "LiteLLM Base URL",
                },
                "defaults": {},
            },
            LlmProviderEnum.GITHUB_COPILOT: {
                "env_vars": ["GITHUB_COPILOT_API_KEY"],
                "config_class": GithubCopilotLlmProvider,
                "prompts": {
                    "GITHUB_COPILOT_API_KEY": "GitHub Copilot API Key",
                    "base_url": "GitHub Copilot Base URL",
                },
                "defaults": {
                    "base_url": "https://api.githubcopilot.com",
                },
            },
        }
        return requirements[provider]

    def collect_provider_inputs(self, provider: LlmProviderEnum) -> dict:
        """Collect user inputs for provider configuration."""
        requirements = self.get_provider_requirements(provider)
        user_inputs = {}

        logger.info(f"\n[2] {provider.value} Configuration:")

        if provider == LlmProviderEnum.GITHUB_COPILOT:
            auth_method = typer.prompt(
                "    Authentication method: 1) Device flow (recommended) 2) API key",
                type=int,
                default=1,
            )
            if auth_method == 1:
                device_flow_data = github_copilot.initiate_device_flow()
                logger.info(
                    f"Please go to {device_flow_data['verification_uri']} and enter the code: "
                    f"{device_flow_data['user_code']}",
                )
                logger.info("Waiting for authorization...")
                github_token = github_copilot.poll_for_token(
                    device_flow_data["device_code"],
                    device_flow_data["interval"],
                )
                if github_token:
                    copilot_token_data = github_copilot.get_copilot_token(github_token)
                    if copilot_token_data:
                        github_copilot.store_credentials(
                            github_token=github_token,
                            copilot_token=copilot_token_data["token"],
                            expires_at=copilot_token_data["expires_at"],
                        )
                        logger.info("✅ GitHub Copilot authenticated successfully.")
                        return {}
                    logger.error("❌ Failed to get Copilot token.")
                    raise typer.Exit(1)
                logger.error("❌ GitHub Copilot authentication failed.")
                raise typer.Exit(1)
            for field, prompt in requirements["prompts"].items():
                default = requirements["defaults"].get(field, "")
                if default:
                    user_input = typer.prompt(f"    {prompt} ({default})", default=default)
                else:
                    user_input = typer.prompt(f"    {prompt} [required]")

                # Validate required fields
                if not user_input and field in requirements["env_vars"]:
                    typer.echo(f"❌ {prompt} is required")
                    raise typer.Exit(1)

                user_inputs[field] = user_input
        else:
            for field, prompt in requirements["prompts"].items():
                default = requirements["defaults"].get(field, "")
                if default:
                    user_input = typer.prompt(f"    {prompt} ({default})", default=default)
                else:
                    user_input = typer.prompt(f"    {prompt} [required]")

                # Validate required fields
                if not user_input and field in requirements["env_vars"]:
                    typer.echo(f"❌ {prompt} is required")
                    raise typer.Exit(1)

                user_inputs[field] = user_input

        return user_inputs

    def create_provider_config(self, provider: LlmProviderEnum, user_inputs: dict) -> dict:
        """Create provider configuration based on user inputs."""
        requirements = self.get_provider_requirements(provider)
        config_class = requirements["config_class"]

        if not config_class:
            return {}  # No additional provider config needed

        # Create provider config instance
        provider_config = {}
        if provider == LlmProviderEnum.AZURE_OPEN_AI:
            provider_config = {
                "azure_openai": {
                    "resource_name": user_inputs["resource_name"],
                    "api_version": user_inputs["api_version"],
                },
            }
        elif provider == LlmProviderEnum.LITE_LLM:
            provider_config = {
                "lite_llm": {
                    "base_url": user_inputs["base_url"],
                },
            }
        elif provider == LlmProviderEnum.GITHUB_COPILOT:
            provider_config = {
                "github_copilot": {
                    "base_url": user_inputs["base_url"],
                },
            }

        return provider_config

    def create_env_vars(self, provider: LlmProviderEnum, user_inputs: dict) -> dict:
        """Create environment variables for provider."""
        requirements = self.get_provider_requirements(provider)
        env_vars = {}

        for env_var in requirements["env_vars"]:
            if env_var in user_inputs:
                env_vars[env_var] = user_inputs[env_var]

        return env_vars


async def validate_configuration_requirements() -> bool:
    """Check if global configuration already exists and is valid."""
    config_paths = ConfigPaths()
    global_config_file = config_paths.get_global_config_dir() / "config.yaml"
    global_env_file = config_paths.get_global_config_dir() / ".env"

    # Check if configuration files exist
    if not global_config_file.exists() or not global_env_file.exists():
        return False

    try:
        # Try to load and validate existing configuration
        with global_config_file.open() as f:
            config_data = yaml.safe_load(f)

        # Basic validation - ensure required sections exist
        if not config_data or "llm" not in config_data:
            return False

        if "default_model" not in config_data["llm"] or "models" not in config_data["llm"]:
            return False

        logger.info("✅ Global configuration found and appears valid")
        return True

    except (OSError, yaml.YAMLError, KeyError) as e:
        logger.debug(f"Error validating existing configuration: {e}")
        return False


async def create_global_config_files(
    provider: LlmProviderEnum,
    user_inputs: dict,
    model_name: str,
    model_alias: str,
) -> None:
    """Create global configuration files."""
    config_paths = ConfigPaths()
    global_dir = config_paths.get_global_config_dir()

    # Ensure global directory exists
    global_dir.mkdir(parents=True, exist_ok=True)

    setup = LLMProviderSetup()

    # Create provider config
    provider_config = setup.create_provider_config(provider, user_inputs)

    # Create default provider configs
    providers_config = {
        "openai": {},
        "azure_openai": None,
        "lite_llm": None,
        "github_copilot": None,
    }

    # Update with user's provider config
    providers_config.update(provider_config)

    # Create model config
    model_config = {
        "name": model_alias,
        "provider": provider.value,
        "model": model_name,
        "temperature": 0.0,
        "max_tokens": None,
        "use_cache": True,
    }

    # Create complete config
    config_data = {
        "llm": {
            "default_model": model_alias,
            "providers": providers_config,
            "models": [model_config],
            "behavior": {
                "use_cache": True,
                "retry_count": 3,
                "timeout": 30,
            },
        },
    }

    # Write config.yaml
    config_file = global_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.safe_dump(config_data, f, default_flow_style=False, indent=2)

    # Create environment variables
    env_vars = setup.create_env_vars(provider, user_inputs)

    # Write .env file
    env_file = global_dir / ".env"
    with env_file.open("w") as f:
        f.write("# AWA Global Configuration Environment Variables\n")
        f.write("# Generated by 'awa init' command\n\n")
        f.writelines(f"{key}={value}\n" for key, value in env_vars.items())

    logger.info(f"✅ Global configuration saved to {global_dir}")
    logger.info("✅ Configuration files created:")
    logger.info(f"  • {config_file}")
    logger.info(f"  • {env_file}")


@app.command(name="init")
def init(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force re-initialization even if config exists"),
    ] = False,
) -> None:
    """Initialize AWA global configuration with interactive setup."""
    init_logging()
    asyncio.run(_init(force=force))


async def _init(force: bool = False) -> None:
    """Initialize AWA global configuration."""
    logger.info(cli_constants.INTRO)
    logger.info("🚀 AWA Configuration Setup")

    # Check if configuration already exists
    if not force and await validate_configuration_requirements():
        logger.info("✅ Global configuration already exists and is valid")
        logger.info("Use 'awa init --force' to reconfigure")
        return

    global_dir = ConfigPaths().get_global_config_dir()
    logger.info(f"Setting up global configuration at: {global_dir}")

    # Step 1: Provider selection
    logger.info("\n[1] Choose your LLM provider:")
    providers = [
        (LlmProviderEnum.OPEN_AI, "OpenAI"),
        (LlmProviderEnum.AZURE_OPEN_AI, "Azure OpenAI"),
        (LlmProviderEnum.AWS_BEDROCK, "AWS Bedrock"),
        (LlmProviderEnum.LITE_LLM, "LiteLLM Proxy"),
        (LlmProviderEnum.GITHUB_COPILOT, "GitHub Copilot"),
    ]

    for i, (_provider_enum, provider_name) in enumerate(providers, 1):
        logger.info(f"    {i}) {provider_name}")

    while True:
        try:
            selection = typer.prompt("\nSelection", type=int)
            if 1 <= selection <= len(providers):
                selected_provider = providers[selection - 1][0]
                break
            typer.echo("❌ Invalid selection. Please choose a number from 1-5.")
        except ValueError:
            typer.echo("❌ Invalid input. Please enter a number.")

    # Step 2: Provider configuration
    setup = LLMProviderSetup()
    user_inputs = setup.collect_provider_inputs(selected_provider)

    # Step 3: Model configuration
    logger.info("\n[3] Model Configuration:")
    model_name = typer.prompt("    Model Name (e.g., gpt-4o, claude-3-sonnet)")
    model_alias = typer.prompt("    Default Model Alias", default=f"my-{selected_provider.value.lower()}-model")

    # Step 4: Validate and create configuration
    try:
        await create_global_config_files(
            selected_provider,
            user_inputs,
            model_name,
            model_alias,
        )

        logger.info("=" * 50)
        logger.info("✅ AWA global configuration setup complete!")
        logger.info("\nNext steps:")
        logger.info("  • Run 'awa start' to begin using AWA")
        logger.info("  • Use 'awa init --force' to modify settings")
        logger.info("  • Local config.yaml files will override global settings for specific projects")

    except Exception as e:
        logger.exception("❌ Configuration setup failed")
        raise typer.Exit(1) from e
