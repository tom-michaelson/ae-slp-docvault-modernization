using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Execute an OpenAI agent with the specified configuration.
        ///
        /// This workflow integrates the OpenAI Agents SDK with AWA's configuration system,
        /// allowing agents to use AWA-configured models (OpenAI, Azure OpenAI, LiteLLM, etc.)
        /// while supporting MCP servers, structured outputs, and agent handoffs.
        /// </summary>
        /// <param name="config">Configuration for the OpenAI agent execution including:
        /// - name: Agent name
        /// - instructions: System instructions for the agent
        /// - model: Model to use (e.g., "gpt-4", configured via AWA)
        /// - input: User input/prompt for the agent
        /// - mcp_servers: Optional list of MCP server names
        /// - agent_tools: Optional list of agent tools/nested agents
        /// - handoffs: Optional list of agent handoffs
        /// - response_format: Optional response format (text/json_schema)
        /// - response_schema: Optional JSON schema for structured outputs
        /// - metadata: Optional metadata dict</param>
        /// <param name="workflowId">Optional workflow ID for the child workflow.
        /// If not provided, a default ID will be generated.</param>
        /// <returns>OpenAIAgentResponse: The result of the agent execution including:
        /// - content: The agent's response content
        /// - execution_id: Unique execution identifier
        /// - agent_name: Name of the agent that executed
        /// - model_used: The model that was used
        /// - execution_time_seconds: Time taken for execution
        /// - metadata: Optional metadata from the config
        /// - handoff_events: List of handoff events if handoffs occurred
        /// - final_agent: Name of the final agent if handoffs occurred</returns>
        public static async Task<OpenAiAgentResponse> OpenaiAgentWorkflow(
            OpenAiAgentConfig config,
            string? workflowId = null)
        {
            var effectiveWorkflowId = workflowId ?? $"openai-agent-{config.Name}-{Temporalio.Workflows.Workflow.Info.WorkflowId}";

            return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<OpenAiAgentResponse>(
                AwaConstants.WorkflowOpenaiAgent,
                new object?[] { config },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    Id = effectiveWorkflowId
                });
        }
    }
}
