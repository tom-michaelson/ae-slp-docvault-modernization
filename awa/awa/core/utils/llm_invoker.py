import asyncio
import importlib.util
import inspect
import os
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

try:
    from azure.identity import AzureCliCredential

    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False

import yaml
from baml_py import ClientRegistry, Collector, Image
from baml_py.baml_py import BamlError
from baml_py.errors import BamlClientFinishReasonError, BamlClientHttpError, BamlValidationError
from baml_py.logging import set_log_level
from fsspec.implementations.local import LocalFileSystem
from loguru._logger import Logger
from pydantic import BaseModel
from temporalio.activity import Info

# from core.llm.baml_hooks.baml_test_generator_hook import BamlTestGeneratorHook
from awa.core import constants
from awa.core.auth import github_copilot
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.app_config import AppConfig
from awa.core.models.config.env_config import EnvConfig
from awa.core.models.config.llm_providers_config import (
    AnthropicLlmProvider,
    AzureOpenAiLlmProvider,
    GithubCopilotLlmProvider,
    GoogleVertexLlmProvider,
    LlmProviderEnum,
)
from awa.core.models.config.model_config import ModelConfig
from awa.core.utils.cache_utils import CacheUtils
from awa.core.utils.config_utils import ConfigUtils
from awa.core.utils.file_system_utils import FileSystemUtils
from awa.sdk.models.baml_image_input_params import BamlImageInputParams
from awa.sdk.models.exceptions import (
    AwaLlmAuthError,
    AwaLlmInvalidRequestError,
    AwaLlmRateLimitError,
    AwaLlmResponseParsingError,
)

T = TypeVar("T", bound=BaseModel | str)
U = TypeVar("U", bound=BaseModel | str)
V = TypeVar("V", bound=BaseModel | str)


@dataclass
class TokenCacheEntry:
    """Cache entry for Azure access tokens."""

    token: str
    expires_at: datetime
    resource_name: str

    def is_expired(self, buffer_minutes: int = 5) -> bool:
        """Check if token is expired with optional buffer time."""
        return datetime.now(UTC) + timedelta(minutes=buffer_minutes) >= self.expires_at


class LlmInvoker:
    def __init__(self, config: AppConfig, baml_src_dir: Path | str | None = None, logger: Logger | None = None) -> None:
        self.logger = logger or get_logger(LoggerComponent.CLI)
        self._config: AppConfig = config
        # Synchronization primitives for thread safety
        self._reload_lock = asyncio.Lock()
        self._active_transforms = 0
        self._active_transforms_lock = asyncio.Lock()
        self._baml_src_dir = baml_src_dir or Path(__file__).parent.parent.parent.parent / "awa" / "baml_src"
        # Cache for Azure credentials
        self._azure_credential_cache: dict[str, TokenCacheEntry] = {}

    def _get_azure_token(self, provider_config: AzureOpenAiLlmProvider) -> str:
        """Get Azure access token for Azure OpenAI, using cache when possible."""
        if not AZURE_IDENTITY_AVAILABLE:
            raise ValueError(
                "Azure Identity package is required for Entra authentication. Install with: pip install azure-identity",
            )

        cache_key = provider_config.resource_name

        # Check if we have a valid cached token
        if cache_key in self._azure_credential_cache:
            cached_entry = self._azure_credential_cache[cache_key]
            if not cached_entry.is_expired():
                self.logger.debug(f"Using cached Azure token for resource {provider_config.resource_name}")
                return cached_entry.token
            # Remove expired entry
            del self._azure_credential_cache[cache_key]
            self.logger.debug(f"Cached Azure token expired for resource {provider_config.resource_name}")

        try:
            # Use AzureCliCredential directly to avoid credential chain noise
            credential = AzureCliCredential()
            token_response = credential.get_token("https://cognitiveservices.azure.com/.default")

            # Cache the token with 45-minute expiration (safe buffer under 60-minute minimum)
            cache_entry = TokenCacheEntry(
                token=token_response.token,
                expires_at=datetime.now(UTC) + timedelta(minutes=45),
                resource_name=provider_config.resource_name,
            )
            self._azure_credential_cache[cache_key] = cache_entry

            self.logger.debug(
                f"Successfully acquired and cached Azure token for resource {provider_config.resource_name}",
            )
            return token_response.token
        except Exception as e:
            raise ValueError(
                f"Failed to get Azure CLI credential token: {e}. Ensure you are logged into Azure CLI with 'az login'.",
            ) from e

    def _clear_azure_token_cache(self, resource_name: str) -> None:
        """Clear cached Azure token for a specific resource."""
        if resource_name in self._azure_credential_cache:
            del self._azure_credential_cache[resource_name]
            self.logger.debug(f"Cleared cached Azure token for resource {resource_name}")

    async def execute_transform(
        self,
        top_level_workflow_type: str,
        top_level_workflow_id: str,
        activity_info: Info,
        model_name: str,
        baml_function_name: str,
        request: T,
        images: list[BamlImageInputParams] | None = None,
    ) -> U:
        # Get model config by matching the name property
        model_config = ConfigUtils.get_model_config(self._config, model_name)

        def serialize_for_cache_key(inner_request: T) -> dict[str, Any]:
            to_serialize_for_cache_key: dict[str, Any] = {}
            if isinstance(inner_request, BaseModel):
                to_serialize_for_cache_key["request"] = inner_request.model_dump()
            else:
                to_serialize_for_cache_key["request"] = inner_request

            if images:
                # Serialize images for cache key by converting each to a dict (model_dump)
                to_serialize_for_cache_key["images"] = [
                    image.model_dump() if isinstance(image, BaseModel) else image for image in images
                ]

            # Find original BAML file content to include in cache key
            # Use absolute path from project root instead of relative path
            # project_root = Path(__file__).parent.parent.parent.parent
            baml_directories = [
                # project_root / "awa" / "baml_src",
                # project_root / "awa" / "baml_dynamic",
                Path(self._baml_src_dir),
            ]
            # Search for the function definition start, including the opening parenthesis
            search_string = f"function {baml_function_name}"
            found_file_content: str | None = None

            try:
                for baml_dir in baml_directories:
                    if found_file_content:  # Stop searching if already found
                        break
                    if not baml_dir.exists():
                        continue
                    for root, _, files in os.walk(baml_dir):
                        if found_file_content:  # Stop walking if already found
                            break
                        for file in files:
                            if file.endswith(".baml"):
                                file_path: Path = Path(root) / file
                                content = FileSystemUtils.read(LocalFileSystem(auto_mkdir=True), file_path)
                                # Simple substring check for the function definition start
                                if f"{search_string}(" in content or f"{search_string} " in content:
                                    found_file_content = content
                                    break  # Found the file, stop searching files in this directory
                        if found_file_content:
                            break
            except Exception as e:  # noqa: BLE001
                self.logger.warning(
                    f"Error while searching for BAML function '{baml_function_name}' for cache key generation: {e}",
                    exc_info=e,
                )

            if found_file_content:
                to_serialize_for_cache_key["_baml_file_content"] = found_file_content
            else:
                # Assign a unique value to prevent accidental cache hits when the BAML file is missing
                to_serialize_for_cache_key["_baml_file_content"] = str(uuid.uuid4())
                self.logger.warning(
                    f"Could not find BAML file containing 'function {baml_function_name}'. "
                    f"Cache key will not include BAML file content. "
                    f"Using a GUID instead to prevent incorrect caching.",
                )

            return to_serialize_for_cache_key

        async def run_baml_function(
            baml_client: Any,  # BamlAsyncClient  # noqa: ANN401
            request: T,
        ) -> U:
            try:
                target_function = getattr(baml_client, baml_function_name)
            except AttributeError as e:
                raise AttributeError(
                    f"BAML function '{baml_function_name}' not found. Double-check that transform.baml matches "
                    "the function name in one of your project BAML files.",  # pylint: disable=line-too-long
                ) from e

            if images:
                for image in images:
                    if image.name in request:
                        raise ValueError(f"Key {image.name} already exists in request")

                    request[image.name] = Image.from_base64(
                        media_type=image.mime_type,
                        base64=image.base64_str,
                    )

            ret: U = await target_function(request)
            return ret

        return await self._run_baml_function(
            top_level_workflow_type=top_level_workflow_type,
            top_level_workflow_id=top_level_workflow_id,
            activity_info=activity_info,
            model_config=model_config,
            request=request,
            baml_function_name=baml_function_name,
            run_baml_function=run_baml_function,
            serialize_for_cache_key=serialize_for_cache_key,
        )

    async def _run_baml_function(  # noqa: PLR0915
        self,
        top_level_workflow_type: str,
        top_level_workflow_id: str,
        activity_info: Info,
        model_config: ModelConfig,
        request: T,
        baml_function_name: str,
        run_baml_function: Callable[[Any, Any, T], Awaitable[U]],
        serialize_for_cache_key: Callable[[T], dict[str, Any]] | None = None,
        parsing_attempt: int = 0,
        current_temperature_override: float | None = None,
        collector: Collector | None = None,
        auth_retry_attempt: int = 0,
    ) -> U:
        to_serialize_for_cache_key = request
        if serialize_for_cache_key:
            to_serialize_for_cache_key = serialize_for_cache_key(request)

        # Determine response type by looking at BAML function
        baml_client, collector = await self._get_baml_client(
            model_config=model_config,
            collector_name=None,
            cache_key=self._get_cache_key(model_config, to_serialize_for_cache_key),
            baml_function_name=baml_function_name,
            temperature_override=current_temperature_override,
            collector=collector,
        )

        response_type = self._determine_response_type(baml_client, baml_function_name)
        cache_key: str = self._get_cache_key(model_config, to_serialize_for_cache_key)
        cached_response: str | None = await self._load_from_cache(cache_key)
        if cached_response and model_config.use_cache is not False:
            try:
                if issubclass(response_type, BaseModel):
                    return response_type.model_validate_json(cached_response)
                if issubclass(response_type, str):
                    return cached_response
                raise ValueError(f"Invalid response type: {response_type}")  # noqa: TRY301
            except Exception:  # noqa: BLE001
                return cached_response

        retry_config = self._config.llm.behavior.auto_retry_parse
        max_attempts = retry_config.max_attempts if retry_config.enabled else 1

        response: U | None = None
        exceptions: list[Exception] = []
        success: bool = False
        try:
            response = await run_baml_function(baml_client, request)
            success = True
        except BamlClientFinishReasonError as bcre:
            exceptions.append(bcre)
            raise
        except BamlValidationError as bve:
            exceptions.append(bve)
            if retry_config.enabled and parsing_attempt < max_attempts - 1:
                next_attempt = parsing_attempt + 1
                next_temperature = model_config.temperature + (next_attempt * retry_config.temperature_increment)
                next_temperature = max(min(next_temperature, 1.0), 0.0)

                self.logger.warning(
                    f"BAML Parse Error Retry {next_attempt}/{max_attempts - 1}. "
                    f"Increasing temperature to {next_temperature:.2f} for next attempt.",
                )

                return await self._run_baml_function(
                    top_level_workflow_type=top_level_workflow_type,
                    top_level_workflow_id=top_level_workflow_id,
                    activity_info=activity_info,
                    model_config=model_config,
                    request=request,
                    baml_function_name=baml_function_name,
                    run_baml_function=run_baml_function,
                    serialize_for_cache_key=serialize_for_cache_key,
                    parsing_attempt=next_attempt,
                    current_temperature_override=next_temperature,
                    collector=collector,
                )

            # pylint: disable=bad-exception-cause
            raise AwaLlmResponseParsingError from bve
        except BamlClientHttpError as bce:
            exceptions.append(bce)
            if bce.status_code in (401, 403):
                # Handle authentication errors with retry for Azure Entra auth
                if (
                    auth_retry_attempt == 0
                    and model_config.provider == LlmProviderEnum.AZURE_OPEN_AI
                    and self._config.llm.providers.azure_openai
                    and self._config.llm.providers.azure_openai.use_entra_auth
                ):
                    # Clear cached token and retry once
                    self._clear_azure_token_cache(self._config.llm.providers.azure_openai.resource_name)
                    self.logger.warning("Azure authentication failed, clearing cache and retrying with fresh token")

                    return await self._run_baml_function(
                        top_level_workflow_type=top_level_workflow_type,
                        top_level_workflow_id=top_level_workflow_id,
                        activity_info=activity_info,
                        model_config=model_config,
                        request=request,
                        baml_function_name=baml_function_name,
                        run_baml_function=run_baml_function,
                        serialize_for_cache_key=serialize_for_cache_key,
                        parsing_attempt=parsing_attempt,
                        current_temperature_override=current_temperature_override,
                        collector=collector,
                        auth_retry_attempt=auth_retry_attempt + 1,
                    )

                # pylint: disable=bad-exception-cause
                raise AwaLlmAuthError(f"Invalid LLM credentials: {bce}") from bce
            if bce.status_code == 429:  # noqa: PLR2004
                raise AwaLlmRateLimitError(str(bce)) from bce
            if bce.status_code == 400:  # noqa: PLR2004
                raise AwaLlmInvalidRequestError(str(bce)) from bce
            raise
        except BamlError as be:
            exceptions.append(be)
            raise
        except Exception as e:
            exceptions.append(e)
            raise
        finally:
            await self._log_baml_execution(  # type: ignore[arg-type]
                top_level_workflow_type=top_level_workflow_type,
                top_level_workflow_id=top_level_workflow_id,
                activity_info=activity_info,
                collector=collector,
                request=(request.model_dump() if isinstance(request, BaseModel) else request),
                response=response.model_dump() if isinstance(response, BaseModel) else response,
                success=success,
                exceptions=exceptions,
                cache_key=cache_key,
            )

        await self._save_to_cache(
            cache_key,
            (response.model_dump_json() if isinstance(response, BaseModel) else response),
        )
        return response  # Success

    def _determine_response_type(self, baml_client: Any, baml_function_name: str) -> type[U]:  # noqa: ANN401
        target_function = getattr(baml_client, baml_function_name)

        # Get the type hints for the function
        try:
            type_hints = get_type_hints(target_function)
            return_type = type_hints.get("return", None)

            # If we got a return type, return it
            if return_type is not None:
                return return_type

        except (AttributeError, NameError, TypeError) as e:
            self.logger.debug(f"Could not extract type hints from BAML function '{baml_function_name}': {e}")

        # Fallback: inspect the function signature
        try:
            sig = inspect.signature(target_function)
            if sig.return_annotation != inspect.Signature.empty:
                return sig.return_annotation
        except (AttributeError, ValueError) as e:
            self.logger.debug(f"Could not extract return annotation from BAML function '{baml_function_name}': {e}")

        # Final fallback - return BaseModel as default
        self.logger.warning(
            f"Could not determine return type for BAML function '{baml_function_name}', defaulting to BaseModel",
        )
        return BaseModel

    def _get_cache_key(self, model_config: ModelConfig, request: dict[str, Any] | BaseModel) -> str:
        request_dict = request
        if isinstance(request_dict, BaseModel):
            request_dict = request_dict.model_dump()
        if not isinstance(request_dict, dict):
            raise TypeError(f"Request is not a dict: {request_dict}")

        cache_key_parts = {
            "_config_provider": model_config.provider,
            "_config_model_config": model_config.model_dump(),
        }
        cache_key_parts.update(request_dict)
        return CacheUtils.hash(cache_key_parts)

    def _get_cache_file_path(self, cache_key: str) -> str:
        return Path(EnvConfig.get_env_config().llm_cache_path) / f"{cache_key}.{constants.CACHE_FILE_EXTENSION}"

    async def _load_from_cache(self, cache_key: str) -> str | None:
        cache_path = self._get_cache_file_path(cache_key)
        if not Path.exists(cache_path):
            return None
        return FileSystemUtils.read(LocalFileSystem(auto_mkdir=True), cache_path)

    async def _save_to_cache(self, cache_key: str, cache_value: str) -> None:
        cache_path = self._get_cache_file_path(cache_key)
        FileSystemUtils.write(LocalFileSystem(auto_mkdir=True), cache_path, cache_value)

    async def _get_baml_client(
        self,
        model_config: ModelConfig,
        collector_name: str | None,
        cache_key: str,  # noqa: ARG002
        baml_function_name: str,  # noqa: ARG002
        temperature_override: float | None = None,  # noqa: ARG002
        collector: Collector | None = None,
        options_override: dict[str, Any] | None = None,
        support_auto_continue: bool = False,
    ) -> tuple[Any, Collector]:
        if not collector_name:
            collector_name = "AWA_Collector"

        provider_name, options = self._get_baml_client_options(model_config)
        client_name = f"AWA_{provider_name}"
        client_registry = ClientRegistry()

        # If we support auto-continue, limit the allowed finish reasons to only allow "stop"
        if support_auto_continue:
            options["finish_reason_allow_list"] = ["stop"]

        # Add metadata for LiteLLM->Langfuse logging
        # TODO AWA-128: Set LiteLLM metadata for tracing
        # if model_config.provider == LlmProviderEnum.LITE_LLM:
        #     logger.info("Adding LiteLLM metdata")
        # options["metadata"] = {"hello": "world"}
        # project_workflow_run_combined = f"{run_state.project_id}:{run_state.process_id}:{run_state.run_id}"
        # tags = [
        #     f"project:{run_state.project_id}",
        #     f"workflow:{run_state.process_id}",
        #     f"run:{run_state.run_id}",
        #     f"session:{run_state.session_id}",
        # ]
        # if task_node:
        #     tags.append(f"task:{task_node.fully_qualified_name}")
        # options["metadata"] = {
        #     "session_id": project_workflow_run_combined,
        #     "trace_id": task_node.id_hash if task_node else project_workflow_run_combined,
        #     "trace_name": task_node.fully_qualified_name if task_node else project_workflow_run_combined,
        #     "generation_name": baml_function_name,
        #     "taskstream": {
        #         "project_id": run_state.project_id,
        #         "workflow_id": run_state.process_id,
        #         "run_id": run_state.run_id,
        #         "session_id": run_state.session_id,
        #         "task_id_user_def": task_node.id.user_def if task_node else None,
        #         "task_id_guid": task_node.id.guid if task_node else None,
        #         "task_id_hash": task_node.id_hash if task_node else None,
        #         "task_fqn": task_node.fully_qualified_name if task_node else None,
        #         "cache_key": cache_key,
        #     },
        #     "tags": tags,
        # }

        if options_override:
            options.update(options_override)

        client_registry.add_llm_client(
            name=client_name,
            provider=provider_name,
            options=options,
            retry_policy="DefaultRetryPolicy",
        )
        client_registry.set_primary(client_name)

        if not collector:
            collector = Collector(name=collector_name)

        # TODO RH: Test generator hook
        # test_file_dir = await HandlesUtils.resolve_handles(
        #     os.path.join("{{taskstream.system_dir}}", "baml_tests"),
        #     run_state=run_state,
        #     task_id=task_node.id if task_node else None,
        # )
        # test_name = f"Test{baml_function_name}"
        # if task_node:
        #     test_name += f"{pascal(task_node.id.user_def, split_on_first_upper=True)}T{task_node.id_hash_hex.lower()}"
        # else:
        #     test_name += f"{CacheUtils.hash(str(round(time.time() * 1000)), True)}"
        # test_file_name = snake(test_name, split_on_first_upper=True)
        # test_generator_hook = BamlTestGeneratorHook(
        #     test_file_dir=test_file_dir,
        #     test_file_name=test_file_name,
        #     test_name=test_name,
        # )

        # client = with_hooks(b.with_options(client_registry=client_registry, collector=collector),
        # [test_generator_hook])

        # Dynamically load BAML client and logging function
        b = self._load_baml_client_module()
        client = b.with_options(client_registry=client_registry, collector=collector)
        set_log_level("INFO")

        return client, collector

    def _get_token_parameter_for_api(self, model_config: ModelConfig) -> dict[str, Any]:
        """Get the appropriate token limit parameter based on API endpoint.

        For GPT-5 models:
        - Responses API uses max_output_tokens
        - Chat Completions API uses max_completion_tokens

        Returns:
            dict: Token parameter dict, e.g., {"max_output_tokens": 65536} or empty dict

        """
        if model_config.use_responses_api:
            if model_config.max_output_tokens:
                self.logger.debug(f"Using max_output_tokens={model_config.max_output_tokens} for Responses API")
                return {"max_output_tokens": model_config.max_output_tokens}
        elif model_config.max_completion_tokens:
            self.logger.debug(
                f"Using max_completion_tokens={model_config.max_completion_tokens} for Chat Completions API",
            )
            return {"max_completion_tokens": model_config.max_completion_tokens}
        return {}

    def _build_gpt5_parameters(self, model_config: ModelConfig) -> dict[str, Any]:
        """Build GPT-5 specific parameters.

        GPT-5 models have different parameters than GPT-4:
        - verbosity: Controls output length and detail (low/medium/high)
        - reasoning_effort: Controls reasoning depth (minimal/low/medium/high)
        - Token parameters depend on API endpoint (see _get_token_parameter_for_api)
        - No temperature parameter (not supported by GPT-5)

        Args:
            model_config: Model configuration

        Returns:
            dict: GPT-5 parameter dict

        """
        options: dict[str, Any] = {}

        # Verbosity (default to medium if not specified)
        verbosity = model_config.verbosity or "medium"
        options["verbosity"] = verbosity
        self.logger.debug(f"GPT-5 verbosity: {verbosity}")

        # Reasoning effort (string values for GPT-5: minimal/low/medium/high)
        if model_config.reasoning_effort:
            options["reasoning_effort"] = model_config.reasoning_effort
            self.logger.debug(f"GPT-5 reasoning_effort: {model_config.reasoning_effort}")

        # Token parameters (different for Responses API vs Chat Completions API)
        token_params = self._get_token_parameter_for_api(model_config)
        options.update(token_params)

        # Log which API is being used
        api_type = "Responses API" if model_config.use_responses_api else "Chat Completions API"
        self.logger.info(f"Using {api_type} for GPT-5 model '{model_config.name}'")

        return options

    def _get_baml_client_options(self, model_config: ModelConfig) -> tuple[str, dict[str, Any]]:  # noqa: PLR0915
        client_name: str = ""
        options: dict[str, Any] = {}

        # Handle GPT-5 specific parameters
        if model_config.is_gpt5_model:
            options.update(self._build_gpt5_parameters(model_config))
        else:
            # GPT-4 and other models
            if model_config.reasoning_effort:
                options["reasoning_effort"] = model_config.reasoning_effort
            if model_config.max_tokens:
                options["max_tokens"] = model_config.max_tokens
            if model_config.temperature:
                options["temperature"] = model_config.temperature

        match model_config.provider:
            case LlmProviderEnum.OPEN_AI:
                client_name = "openai"
                options["api_key"] = self._config.llm.providers.openai.api_key
                options["model"] = model_config.model
                base_url = self._config.llm.providers.openai.base_url
                if base_url:
                    options["base_url"] = base_url
            case LlmProviderEnum.AZURE_OPEN_AI:
                client_name = "azure-openai"
                provider_config: AzureOpenAiLlmProvider | None = self._config.llm.providers.azure_openai or None
                if not provider_config:
                    raise ValueError("Azure OpenAI provider config not found")

                if provider_config.use_entra_auth:
                    # Use Entra ID authentication with bearer token
                    # Get a fresh token and pass it via Authorization header
                    token = self._get_azure_token(provider_config)
                    options["headers"] = {"Authorization": f"Bearer {token}"}
                else:
                    # Use API key authentication (if available)
                    api_key = provider_config.api_key
                    if api_key:
                        options["api_key"] = api_key

                # Determine API endpoint based on model configuration
                # Azure OpenAI supports two different API endpoints:
                # 1. Responses API (/responses) - New API for GPT-5 reasoning models with stateful interactions
                # 2. Chat Completions API (/chat/completions) - Traditional API for GPT-4 and GPT-5
                #
                # IMPORTANT: BAML requires different configuration approaches:
                # - Responses API: Use base_url with full URL (don't set resource_name/deployment_id)
                # - Chat Completions API: Use resource_name + deployment_id + api_version (don't set base_url)
                if model_config.use_responses_api:
                    # For Responses API, construct full base_url
                    # Format: https://{resource}.{domain}/openai/deployments/{deployment}/responses?api-version={version}
                    api_endpoint = "responses"
                    base_url = f"https://{provider_config.resource_name}.{provider_config.domain}/openai/deployments/{model_config.model}/responses?api-version={provider_config.api_version}"
                    options["base_url"] = base_url
                    # Don't set resource_name, deployment_id, or api_version when using base_url
                    # (BAML will error if both base_url and resource_name/deployment_id are set)

                    self.logger.info(f"Azure OpenAI Responses API endpoint: {base_url}")
                else:
                    # For Chat Completions API, use standard BAML configuration
                    # BAML will construct: https://{resource}.{domain}/openai/deployments/{deployment}/chat/completions?api-version={version}
                    api_endpoint = "chat/completions"
                    options["resource_name"] = provider_config.resource_name
                    options["deployment_id"] = model_config.model
                    options["api_version"] = provider_config.api_version

                    # Log the endpoint that will be constructed by BAML
                    constructed_endpoint = f"https://{provider_config.resource_name}.{provider_config.domain}/openai/deployments/{model_config.model}/{api_endpoint}?api-version={provider_config.api_version}"
                    self.logger.info(f"Azure OpenAI Chat Completions endpoint: {constructed_endpoint}")
            case LlmProviderEnum.AWS_BEDROCK:
                client_name = "aws-bedrock"

                # Remove keys that must be in a different structure for Bedrock
                if "reasoning_effort" in options:
                    options.pop("reasoning_effort")
                if "max_tokens" in options:
                    options.pop("max_tokens")
                if "temperature" in options:
                    options.pop("temperature")

                options["model"] = model_config.model
                options["inference_configuration"] = {}
                if model_config.max_tokens:
                    options["inference_configuration"]["max_tokens"] = model_config.max_tokens
                if model_config.temperature:
                    options["inference_configuration"]["temperature"] = model_config.temperature
                # TODO RH: Bedrock reasoning effort
            case LlmProviderEnum.GOOGLE_VERTEX:
                client_name = "vertex-ai"
                provider_config: GoogleVertexLlmProvider | None = self._config.llm.providers.google_vertex or None
                if not provider_config:
                    raise ValueError("Google Vertex provider config not found")

                options["model"] = model_config.model
                options["location"] = provider_config.location

                # Remove keys that must be in a different structure for Vertex
                if "reasoning_effort" in options:
                    options.pop("reasoning_effort")
                if "max_tokens" in options:
                    options.pop("max_tokens")
                if "temperature" in options:
                    options.pop("temperature")

                options["generationConfig"] = {}
                if model_config.max_tokens:
                    options["generationConfig"]["maxOutputTokens"] = model_config.max_tokens
                if model_config.temperature:
                    options["generationConfig"]["temperature"] = model_config.temperature

                # Add project_id if specified in config
                if provider_config.project_id:
                    options["project_id"] = provider_config.project_id

                # Add credentials path if specified (GOOGLE_APPLICATION_CREDENTIALS will be used by default otherwise)
                if provider_config.google_application_credentials:
                    options["credentials"] = provider_config.google_application_credentials
            case LlmProviderEnum.LITE_LLM:
                if not self._config.llm.providers.lite_llm:
                    raise ValueError("LiteLLM provider config not found")
                client_name = "openai-generic"
                options["base_url"] = self._config.llm.providers.lite_llm.base_url
                options["model"] = model_config.model
                if self._config.llm.providers.lite_llm.api_key:
                    options["api_key"] = self._config.llm.providers.lite_llm.api_key
            case LlmProviderEnum.GITHUB_COPILOT:
                provider_config: GithubCopilotLlmProvider | None = self._config.llm.providers.github_copilot or None
                if not provider_config:
                    provider_config = GithubCopilotLlmProvider()
                client_name = "openai-generic"
                options["api_key"] = provider_config.get_api_key()
                options["base_url"] = provider_config.base_url
                options["model"] = model_config.model
                # Add required GitHub Copilot headers
                options["headers"] = {
                    "User-Agent": github_copilot.USER_AGENT,
                    "Editor-Version": "vscode/1.99.3",
                    "Editor-Plugin-Version": "copilot-chat/0.26.7",
                    "Copilot-Integration-Id": "vscode-chat",
                }
            case LlmProviderEnum.ANTHROPIC:
                client_name = "anthropic"
                provider_config: AnthropicLlmProvider | None = self._config.llm.providers.anthropic
                if not provider_config:
                    # Create a default provider config if not specified
                    provider_config = AnthropicLlmProvider()
                options["api_key"] = provider_config.api_key
                options["model"] = model_config.model
                if provider_config.base_url:
                    options["base_url"] = provider_config.base_url

        return client_name, options

    async def _log_baml_execution(
        self,
        top_level_workflow_type: str,
        top_level_workflow_id: str,
        activity_info: Info,
        collector: Collector,
        request: dict[str, Any],
        response: dict[str, Any],
        success: bool,
        exceptions: list[Exception],
        cache_key: str,
    ) -> None:
        log_data = {
            "success": success,
            "cache_key": cache_key,
            "request": request,
            "response": response,
            "exceptions": exceptions,
            "calls": [],
        }

        sortable_start_time = LlmInvoker.utc_ms_to_sortable_timestamp(time.time() * 1000)
        function_name = "UNKNOWN"
        baml_log_data = {
            "temporal": {
                "task_queue": activity_info.task_queue,
                "workflow_type": activity_info.workflow_type,
                "workflow_id": activity_info.workflow_id,
                "workflow_run_id": activity_info.workflow_run_id,
                "activity_type": activity_info.activity_type,
                "activity_id": activity_info.activity_id,
                "attempt": activity_info.attempt,
            },
        }

        if collector.last:
            try:
                baml_log = collector.last
                function_name = baml_log.function_name
                sortable_start_time = LlmInvoker.utc_ms_to_sortable_timestamp(baml_log.timing.start_time_utc_ms)
                baml_log_data = {
                    "function_name": baml_log.function_name,
                    "raw_llm_response": baml_log.raw_llm_response,
                    "duration": baml_log.timing.duration_ms,
                    "metadata": baml_log.metadata,
                    "input_tokens": baml_log.usage.input_tokens,
                    "output_tokens": baml_log.usage.output_tokens,
                    "calls": [],
                }

                for call in baml_log.calls:
                    call_log = {
                        "client_name": call.client_name,
                        "provider": call.provider,
                    }
                    if call.http_request:
                        call_log["http_request"] = {
                            "id": call.http_request.id,
                            "url": call.http_request.url,
                            "method": call.http_request.method,
                            "headers": call.http_request.headers,
                            "body": call.http_request.body.json(),
                        }
                    if call.http_response:
                        self.logger.warning(f"Response status: {call.http_response.status}")
                        self.logger.warning(f"Response body: {call.http_response.body.text()}")
                        call_log["http_response"] = {
                            "status": call.http_response.status,
                            "headers": call.http_response.headers,
                            "body": call.http_response.body.json(),
                        }
                    baml_log_data["calls"].append(call_log)
            except Exception:
                self.logger.exception("Error getting last BAML log")

        log_data.update(baml_log_data)

        failure_part = "_failure" if not success else ""
        filename = f"{sortable_start_time}_{function_name}{failure_part}.yaml"

        # Get the project root directory and construct the proper log path
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / "logs" / "workflows" / top_level_workflow_type / top_level_workflow_id / "llm"
        log_path = log_dir / filename

        yaml.add_representer(str, LlmInvoker._str_presenter)
        FileSystemUtils.write(
            LocalFileSystem(auto_mkdir=True),
            str(log_path),
            yaml.dump(
                log_data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
                width=float("inf"),
            ),
        )

    @staticmethod
    def utc_ms_to_sortable_timestamp(timestamp_ms: int) -> str:
        """Convert a UTC millisecond timestamp to a sortable string like YYYYMMDD_HHMMSS_ms."""
        ms = int(timestamp_ms) % 1000
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=UTC)
        return f"{dt.strftime('%Y%m%d_%H%M%S')}_{ms:03d}"

    @staticmethod
    def _str_presenter(dumper, data) -> Any:  # noqa: ANN001, ANN401
        if data.count("\n") > 0:
            data = "\n".join([line.rstrip() for line in data.splitlines()])
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    @staticmethod
    def _convert_messages_for_cost_calculation(messages: list[dict[str, str]]) -> list[dict[str, str]]:
        return [{"role": "user", "content": message["content"]} for message in messages]

    @staticmethod
    def _map_model_name(model_name: str) -> str:
        stripped_model_name = model_name
        if model_name.startswith("arn:aws:bedrock:"):
            stripped_model_name = model_name.split("/")[-1]

        match stripped_model_name:
            case "anthropic.claude-3-5-sonnet-20240620-v1:0":
                return "claude-3-5-sonnet-20240620"
            case "us.anthropic.claude-3-5-sonnet-20240620-v1:0":
                return "claude-3-5-sonnet-20240620"
            case "anthropic.claude-3-7-sonnet-20250219-v1:0":
                return "claude-3-7-sonnet-20250219"
            case "us.anthropic.claude-3-7-sonnet-20250219-v1:0":
                return "claude-3-7-sonnet-20250219"
            case "anthropic.claude-sonnet-4-20250514-v1:0":
                return "claude-sonnet-4-20250514"
            case _:
                return stripped_model_name

    def _load_baml_client_module(self) -> tuple[Any, Any]:
        """Dynamically load the BAML client module and extract the 'b' client and 'set_log_level' function.

        Returns:
            tuple: (b_client, set_log_level_function)

        """
        # Determine the baml_client directory path based on baml_src_dir
        baml_src_path = Path(self._baml_src_dir)

        # The baml_client directory is typically a sibling of baml_src
        baml_client_path = baml_src_path.parent / "baml_client"

        # Check if baml_client directory exists
        if not baml_client_path.exists():
            raise FileNotFoundError(
                f"BAML client directory not found at {baml_client_path}. "
                f"Make sure BAML has been generated for the project.",
            )

        # Look for the main client module (typically __init__.py or client.py)
        init_file = baml_client_path / "__init__.py"
        client_file = baml_client_path / "client.py"

        module_file = None
        if init_file.exists():
            module_file = init_file
        elif client_file.exists():
            module_file = client_file
        else:
            raise FileNotFoundError(
                f"BAML client module not found in {baml_client_path}. Expected __init__.py or client.py",
            )

        # Create a unique module name to avoid conflicts
        module_name = f"baml_client_{hash(str(baml_client_path))}"

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load BAML client module from {module_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        b_client = module.b

        return b_client
