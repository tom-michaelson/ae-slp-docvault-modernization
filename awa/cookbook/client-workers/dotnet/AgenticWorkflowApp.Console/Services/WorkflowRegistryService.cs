using System.Reflection;
using AgenticWorkflowApp.Console.Configuration;
using AgenticWorkflowApp.Console.Models;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace AgenticWorkflowApp.Console.Services;

/// <summary>
/// Main orchestrator service for workflow and activity discovery and registration.
/// Now uses specialized services for each responsibility, focusing on coordination.
/// </summary>
public class WorkflowRegistryService : IHostedService
{
    private readonly WorkflowDiscoveryService _discoveryService;
    private readonly WorkerRegistrationClient _registrationClient;
    private readonly AwaCoreConfiguration _coreConfiguration;
    private readonly TemporalConfiguration _temporalConfiguration;
    private readonly ILogger<WorkflowRegistryService> _logger;

    public WorkflowRegistryService(
        WorkflowDiscoveryService discoveryService,
        WorkerRegistrationClient registrationClient,
        IOptions<TemporalConfiguration> temporalConfiguration,
        IOptions<AwaCoreConfiguration> coreConfiguration,
        ILogger<WorkflowRegistryService> logger)
    {
        _discoveryService = discoveryService;
        _registrationClient = registrationClient;
        _temporalConfiguration = temporalConfiguration.Value;
        _coreConfiguration = coreConfiguration.Value;
        _logger = logger;
    }

    /// <summary>
    /// Discovered workflow types
    /// </summary>
    public IEnumerable<Type> DiscoveredWorkflows { get; private set; } = [];

    /// <summary>
    /// Discovered activity methods
    /// </summary>
    public IEnumerable<MethodInfo> DiscoveredActivities { get; private set; } = [];

    /// <summary>
    /// Workflow information for registration
    /// </summary>
    public List<WorkflowInfo> WorkflowInfoList { get; private set; } = [];

    /// <summary>
    /// Activity information for registration
    /// </summary>
    public List<ActivityInfo> ActivityInfoList { get; private set; } = [];

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Starting workflow registry service...");

        try
        {
            // Validate configuration at startup
            _coreConfiguration.Validate();
            _logger.LogDebug("Configuration validation passed");

            if (!_coreConfiguration.EnableAutoDiscovery)
            {
                _logger.LogInformation("Auto-discovery is disabled, skipping workflow and activity discovery");
                return;
            }

            // Perform discovery and registration
            await RegisterWorkflowsAndActivitiesAsync(cancellationToken);

            _logger.LogInformation("Workflow registry service started successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to start workflow registry service");
            throw; // Always fail fast - registration failures must be addressed
        }
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Stopping workflow registry service...");
        return Task.CompletedTask;
    }

    /// <summary>
    /// Main orchestration method for discovering and registering workflows and activities.
    /// Now delegates to specialized services for cleaner separation of concerns.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token</param>
    public async Task RegisterWorkflowsAndActivitiesAsync(CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Starting workflow and activity registration process...");

        try
        {
            // Step 1: Get assemblies to scan
            var assemblies = WorkflowDiscoveryService.GetDefaultAssembliesToScan();

            // Step 2: Perform discovery and metadata building
            var (workflowInfoList, activityInfoList) = _discoveryService.DiscoverAndBuildWorkflowInfo(
                assemblies, _temporalConfiguration.TaskQueue);

            // Update public properties for backward compatibility
            DiscoveredWorkflows = workflowInfoList.Select(w => w.WorkflowType);
            DiscoveredActivities = activityInfoList.Select(a => a.Method);
            WorkflowInfoList = workflowInfoList;
            ActivityInfoList = activityInfoList;

            // Step 3: Register with AWA API
            var registrationSuccess = await _registrationClient.RegisterWithApiAsync(
                workflowInfoList, activityInfoList, cancellationToken);

            _logger.LogInformation("Workflow and activity registration completed successfully. API registration: {RegistrationStatus}",
                registrationSuccess ? "Success" : "Skipped/Failed");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed during workflow and activity registration");
            throw;
        }
    }


    /// <summary>
    /// Get registration details for logging.
    /// Delegates to the registration client for implementation.
    /// </summary>
    /// <returns>Formatted string with registration details</returns>
    public string GetRegistrationDetails()
    {
        return _registrationClient.GetRegistrationDetails(WorkflowInfoList, ActivityInfoList);
    }
}
