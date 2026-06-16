using System.Reflection;
using AgenticWorkflowApp.Console.Configuration;
using AgenticWorkflowApp.Console.Converters;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Temporalio.Converters;
using Temporalio.Extensions.Hosting;

namespace AgenticWorkflowApp.Console.Extensions;

/// <summary>
/// Builder for configuring Temporal worker with discovered workflows and activities.
/// </summary>
public static class TemporalWorkerBuilder
{
    /// <summary>
    /// Configure the Temporal worker with discovered types.
    /// This avoids creating service providers during configuration.
    /// </summary>
    /// <param name="services">Service collection</param>
    /// <param name="configuration">Configuration instance</param>
    /// <param name="workflows">Discovered workflow types</param>
    /// <param name="activities">Discovered activity methods</param>
    public static void ConfigureTemporalWorker(
        IServiceCollection services,
        IConfiguration configuration,
        IEnumerable<Type> workflows,
        IEnumerable<MethodInfo> activities)
    {
        var temporalConfig = configuration.GetSection(TemporalConfiguration.SectionName)
            .Get<TemporalConfiguration>() ?? new TemporalConfiguration();

        var workflowList = workflows.ToList();
        var activityList = activities.ToList();

        // Configure the Temporal worker with discovered types using dynamic registration
        var builder = services
            .AddHostedTemporalWorker(
                clientTargetHost: temporalConfig.ClientTargetHost,
                clientNamespace: temporalConfig.ClientNamespace,
                taskQueue: temporalConfig.TaskQueue)
            .ConfigureOptions(x =>
                x.ClientOptions!.DataConverter = DataConverter.Default with
                {
                    PayloadConverter = new CamelCasePayloadConverter()
                }
            );

        // Register discovered workflows dynamically
        foreach (var workflowType in workflowList)
        {
            builder.AddWorkflow(workflowType);
        }

        // Register discovered activity types dynamically
        var activityTypes = activityList
            .Select(m => m.DeclaringType!)
            .Where(t => t != null)
            .Distinct();

        foreach (var activityType in activityTypes)
        {
            builder.AddScopedActivities(activityType);
        }

        // Add post-configuration logging without creating service provider
        services.AddSingleton<ITemporalWorkerConfigurationLogger>(provider =>
            new TemporalWorkerConfigurationLogger(
                provider.GetRequiredService<ILogger<TemporalWorkerConfigurationLogger>>(),
                workflowList,
                activityList));
    }
}

/// <summary>
/// Service for logging Temporal worker configuration details.
/// This allows us to log after DI is properly configured.
/// </summary>
public interface ITemporalWorkerConfigurationLogger
{
    void LogConfiguration();
}

public class TemporalWorkerConfigurationLogger : ITemporalWorkerConfigurationLogger
{
    private readonly ILogger<TemporalWorkerConfigurationLogger> _logger;
    private readonly IReadOnlyList<Type> _workflows;
    private readonly IReadOnlyList<MethodInfo> _activities;

    public TemporalWorkerConfigurationLogger(
        ILogger<TemporalWorkerConfigurationLogger> logger,
        IReadOnlyList<Type> workflows,
        IReadOnlyList<MethodInfo> activities)
    {
        _logger = logger;
        _workflows = workflows;
        _activities = activities;
    }

    public void LogConfiguration()
    {
        _logger.LogInformation("Discovery validation completed");
        _logger.LogInformation("Discovered {WorkflowCount} workflows:", _workflows.Count);

        foreach (var workflow in _workflows)
        {
            var attr = workflow.GetCustomAttribute<Temporalio.Workflows.WorkflowAttribute>();
            _logger.LogInformation("  Class: {ClassName} -> Attribute: {AttributeName}",
                workflow.Name, attr?.Name ?? "None");
        }

        _logger.LogInformation("Discovered {ActivityCount} activities:", _activities.Count);
        foreach (var activity in _activities)
        {
            var attr = activity.GetCustomAttribute<Temporalio.Activities.ActivityAttribute>();
            _logger.LogInformation("  Method: {TypeName}.{MethodName} -> Attribute: {AttributeName}",
                activity.DeclaringType?.Name, activity.Name, attr?.Name ?? "None");
        }

        _logger.LogInformation("Temporal worker configured with discovered workflows and activities");
    }
}
