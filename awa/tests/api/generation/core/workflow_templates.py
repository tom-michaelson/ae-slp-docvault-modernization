"""Workflow template providers for test data generation."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowTemplate:
    """Represents a workflow template for test data generation."""

    def __init__(
        self,
        description: str,
        workflow_name: str,
        input_data: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.description = description
        self.workflow_name = workflow_name
        self.input_data = input_data
        self.metadata = metadata or {}

    def to_payload(self) -> dict[str, Any]:
        """Convert template to test payload format."""
        return {
            "description": self.description,
            "payload": {
                "name": self.workflow_name,
                "input": self.input_data,
            },
        }


class WorkflowTemplateProvider(ABC):
    """Abstract base class for workflow template providers."""

    @abstractmethod
    def get_templates(self) -> list[WorkflowTemplate]:
        """Get workflow templates provided by this provider."""

    @abstractmethod
    def get_supported_workflows(self) -> list[str]:
        """Get list of supported workflow names."""


class AutoWorkflowTemplateProvider(WorkflowTemplateProvider):
    """Auto-generated provider for workflows without custom providers."""

    def __init__(self, workflow_name: str) -> None:
        """Initialize auto-generated provider.

        Args:
            workflow_name: Name of the workflow to generate templates for

        """
        self.workflow_name = workflow_name

    def get_templates(self) -> list[WorkflowTemplate]:
        """Get auto-generated templates for the workflow."""
        return [
            WorkflowTemplate(
                description=f"Auto-generated basic template for {self.workflow_name}",
                workflow_name=self.workflow_name,
                input_data='{"input": "basic_test_data"}',
                metadata={"category": "auto_generated", "complexity": "basic"},
            ),
        ]

    def get_supported_workflows(self) -> list[str]:
        """Get list of supported workflow names."""
        return [self.workflow_name]


class HelloHumanTemplateProvider(WorkflowTemplateProvider):
    """Template provider for Hello Human workflow."""

    def get_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                description="Hello Human workflow with basic name",
                workflow_name="awa-hello-human",
                input_data='{"name": "TestUser"}',
                metadata={"category": "basic", "complexity": "simple"},
            ),
            WorkflowTemplate(
                description="Hello Human workflow with special characters",
                workflow_name="awa-hello-human",
                input_data='{"name": "María José"}',
                metadata={"category": "edge_case", "complexity": "simple"},
            ),
        ]

    def get_supported_workflows(self) -> list[str]:
        return ["awa-hello-human"]


class HelloWorldTemplateProvider(WorkflowTemplateProvider):
    """Template provider for Hello World workflow."""

    def get_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                description="Hello World workflow with simple input",
                workflow_name="awa-hello-world",
                input_data='{"name": "World"}',
                metadata={"category": "basic", "complexity": "simple"},
            ),
        ]

    def get_supported_workflows(self) -> list[str]:
        return ["awa-hello-world"]


class TransformTemplateProvider(WorkflowTemplateProvider):
    """Template provider for Transform workflow."""

    def get_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                description="Transform workflow with basic task",
                workflow_name="awa-transform",
                input_data=(
                    '{"task": "Summarize this text", '
                    '"inputs": [{"id": "doc1", "content": "This is a sample document for testing purposes."}], '
                    '"role": "Assistant"}'
                ),
                metadata={"category": "basic", "complexity": "medium"},
            ),
        ]

    def get_supported_workflows(self) -> list[str]:
        return ["awa-transform"]


class BuildPromptTemplateProvider(WorkflowTemplateProvider):
    """Template provider for Build Prompt workflow."""

    def get_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                description="Build Prompt workflow",
                workflow_name="awa-build-prompt",
                input_data='{"template": "Hello {{name}}", "variables": {"name": "Test"}}',
                metadata={"category": "basic", "complexity": "medium"},
            ),
        ]

    def get_supported_workflows(self) -> list[str]:
        return ["awa-build-prompt"]


class ExecuteAgentTemplateProvider(WorkflowTemplateProvider):
    """Template provider for Execute Agent workflow."""

    def get_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                description="Execute Agent workflow",
                workflow_name="awa-execute-agent",
                input_data='{"agent_mode": "claude", "task": "Write a simple hello function", "context": ""}',
                metadata={"category": "basic", "complexity": "high"},
            ),
        ]

    def get_supported_workflows(self) -> list[str]:
        return ["awa-execute-agent"]


class WorkflowTemplateRegistry:
    """Registry for workflow template providers."""

    def __init__(self) -> None:
        self.providers: list[WorkflowTemplateProvider] = []
        self._setup_default_providers()

    def _setup_default_providers(self) -> None:
        """Set up providers using hybrid discovery system."""
        # Manual providers (existing)
        manual_providers = [
            HelloHumanTemplateProvider(),
            HelloWorldTemplateProvider(),
            TransformTemplateProvider(),
            BuildPromptTemplateProvider(),
            ExecuteAgentTemplateProvider(),
        ]

        # Get workflow names that already have manual providers
        manual_workflow_names = set()
        for provider in manual_providers:
            manual_workflow_names.update(provider.get_supported_workflows())

        # Add manual providers first
        self.providers.extend(manual_providers)

        # Auto-discover remaining workflows
        try:
            from awa.core.utils.temporal_discovery import TemporalDiscovery

            discovery = TemporalDiscovery()
            workflows = discovery.discover_workflows_only()

            for workflow_class in workflows:
                workflow_name = self._extract_workflow_name(workflow_class)

                # Only create auto provider if no manual provider exists
                if workflow_name and workflow_name not in manual_workflow_names:
                    auto_provider = AutoWorkflowTemplateProvider(workflow_name)
                    self.providers.append(auto_provider)
                    logger.debug(f"Auto-generated provider for: {workflow_name}")

        except ImportError:
            logger.warning("Failed to auto-discover workflows, using manual providers only")

    def register_provider(self, provider: WorkflowTemplateProvider) -> None:
        """Register a custom workflow template provider.

        Args:
            provider: Workflow template provider to register

        """
        self.providers.append(provider)

    def _extract_workflow_name(self, workflow_class: type) -> str | None:
        """Extract workflow name from class.

        Args:
            workflow_class: Workflow class to extract name from

        Returns:
            Extracted workflow name or None if extraction fails

        """
        try:
            # Get name from Temporal definition if available
            if hasattr(workflow_class, "__temporal_workflow_definition"):
                definition = workflow_class.__temporal_workflow_definition
                if hasattr(definition, "name") and definition.name:
                    return definition.name

            # Fallback: convert class name
            class_name = workflow_class.__name__
            class_name = class_name.removesuffix("Workflow")

            # Simple conversion to kebab-case
            name = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", class_name)
            name = re.sub("([a-z0-9])([A-Z])", r"\1-\2", name).lower()
            return f"awa-{name}"

        except (AttributeError, TypeError):
            return None

    def get_all_templates(self) -> list[WorkflowTemplate]:
        """Get all workflow templates from all providers.

        Returns:
            List of all workflow templates

        """
        templates = []
        for provider in self.providers:
            try:
                templates.extend(provider.get_templates())
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed to provide templates: {e}")
        return templates

    def get_templates_for_workflow(self, workflow_name: str) -> list[WorkflowTemplate]:
        """Get templates for a specific workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of templates for the workflow

        """
        templates = []
        for provider in self.providers:
            if workflow_name in provider.get_supported_workflows():
                try:
                    templates.extend(provider.get_templates())
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Provider {provider.__class__.__name__} failed for workflow {workflow_name}: {e}")
        return templates

    def get_supported_workflows(self) -> list[str]:
        """Get list of all supported workflow names.

        Returns:
            List of supported workflow names

        """
        workflows = set()
        for provider in self.providers:
            try:
                workflows.update(provider.get_supported_workflows())
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed to list workflows: {e}")
        return sorted(workflows)

    def get_workflow_specific_variants(self) -> list[dict[str, Any]]:
        """Get workflow-specific variants for test data generation.

        Returns:
            List of workflow-specific payload variants

        """
        variants = []
        for template in self.get_all_templates():
            try:
                variants.append(template.to_payload())
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to convert template to payload: {e}")
        return variants
