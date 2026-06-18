using System.Reflection;
using AgenticWorkflowApp.Console.Configuration;
using AgenticWorkflowApp.Console.Converters;
using AgenticWorkflowApp.Console.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http;
using Microsoft.Extensions.Logging;
using Polly;
using Polly.Extensions.Http;
using Temporalio.Converters;
using Temporalio.Extensions.Hosting;

namespace AgenticWorkflowApp.Console.Extensions;

/// <summary>
/// Extension methods for configuring workflow discovery and registration services.
/// </summary>
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Add workflow discovery and registration services to the DI container.
    /// </summary>
    /// <param name="services">The service collection</param>
    /// <param name="configuration">Configuration instance</param>
    /// <returns>The service collection for chaining</returns>
    public static IServiceCollection AddWorkflowDiscovery(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Register configuration
        services.Configure<AwaCoreConfiguration>(
            configuration.GetSection(AwaCoreConfiguration.SectionName));
        services.Configure<TemporalConfiguration>(
            configuration.GetSection(TemporalConfiguration.SectionName));

        // Register core services
        services.AddSingleton<WorkflowDiscoveryService>();

        // Register HTTP client with Polly resilience policies
        services.AddHttpClient<WorkerRegistrationClient>()
            .AddPolicyHandler((serviceProvider, request) =>
            {
                // Get configuration
                var coreConfig = configuration.GetSection(AwaCoreConfiguration.SectionName)
                    .Get<AwaCoreConfiguration>() ?? new AwaCoreConfiguration();

                var logger = serviceProvider.GetService<ILogger<WorkerRegistrationClient>>();

                // Create retry policy with exponential backoff
                return HttpPolicyExtensions
                    .HandleTransientHttpError() // Handles HttpRequestException and 5XX, 408 status codes
                    .OrResult(msg => !msg.IsSuccessStatusCode) // Handle non-success status codes
                    .WaitAndRetryAsync(
                        coreConfig.RetryAttempts,
                        retryAttempt => TimeSpan.FromMilliseconds(
                            coreConfig.RetryDelayMs * Math.Pow(2, retryAttempt - 1)),
                        onRetry: (outcome, timespan, retryCount, context) =>
                        {
                            logger?.LogWarning("HTTP retry attempt {RetryCount} after {Delay}ms delay. Reason: {Reason}",
                                retryCount, timespan.TotalMilliseconds,
                                outcome.Exception?.Message ?? outcome.Result?.StatusCode.ToString() ?? "Unknown");
                        });
            })
            .AddPolicyHandler((serviceProvider, request) =>
            {
                // Get configuration for timeout
                var coreConfig = configuration.GetSection(AwaCoreConfiguration.SectionName)
                    .Get<AwaCoreConfiguration>() ?? new AwaCoreConfiguration();

                // Add timeout policy
                return Policy.TimeoutAsync<HttpResponseMessage>(coreConfig.HttpTimeoutSeconds);
            });

        // Register the main orchestrator as a hosted service
        services.AddHostedService<WorkflowRegistryService>();

        return services;
    }

    /// <summary>
    /// Add complete workflow discovery and Temporal worker configuration in a single call.
    /// This replaces the complex setup in Program.cs with a clean, single-method approach.
    /// </summary>
    /// <param name="services">Service collection</param>
    /// <param name="configuration">Application configuration</param>
    /// <returns>Service collection for chaining</returns>
    public static IServiceCollection AddWorkflowSystem(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Add all workflow discovery services
        services.AddWorkflowDiscovery(configuration);

        // Perform discovery and configure Temporal worker
        ConfigureTemporalWorkerWithDiscovery(services, configuration);

        return services;
    }

    /// <summary>
    /// Internal method to handle discovery and Temporal worker configuration.
    /// This encapsulates the complex logic that was previously in Program.cs.
    /// </summary>
    private static void ConfigureTemporalWorkerWithDiscovery(
        IServiceCollection services,
        IConfiguration configuration)
    {
        // Create temporary logger for startup discovery
        using var tempLoggerFactory = LoggerFactory.Create(builder =>
            builder.AddConsole().SetMinimumLevel(LogLevel.Information));
        var tempLogger = tempLoggerFactory.CreateLogger<WorkflowDiscoveryService>();

        // Perform initial discovery for Temporal worker configuration
        var discoveryService = new WorkflowDiscoveryService(tempLogger);
        var assemblies = WorkflowDiscoveryService.GetDefaultAssembliesToScan();
        var (workflows, activities) = discoveryService.DiscoverWorkflowsAndActivities(assemblies);

        // Register discovered workflows and activities with Temporal worker
        TemporalWorkerRegistrationHelper.RegisterDiscoveredWorkflowsAndActivities(services, configuration, workflows, activities);

        tempLogger.LogInformation(
            "Workflow system configured with {WorkflowCount} workflows and {ActivityCount} activities",
            workflows.Count(), activities.Count());
    }


}

/// <summary>
/// Helper class for registering discovered workflows and activities with Temporal worker.
/// </summary>
public static class TemporalWorkerRegistrationHelper
{
    /// <summary>
    /// Register discovered workflows and activities with the Temporal worker.
    /// Uses a cleaner pattern that avoids creating service providers during configuration.
    /// </summary>
    /// <param name="services">Service collection</param>
    /// <param name="configuration">Configuration instance</param>
    /// <param name="workflows">Discovered workflow types</param>
    /// <param name="activities">Discovered activity methods</param>
    public static void RegisterDiscoveredWorkflowsAndActivities(
        IServiceCollection services,
        IConfiguration configuration,
        IEnumerable<Type> workflows,
        IEnumerable<MethodInfo> activities)
    {
        TemporalWorkerBuilder.ConfigureTemporalWorker(services, configuration, workflows, activities);
    }
}
