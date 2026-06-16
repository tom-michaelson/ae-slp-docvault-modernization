using System.Text;
using System.Text.Json;
using AgenticWorkflowApp.Console.Configuration;
using AgenticWorkflowApp.Console.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace AgenticWorkflowApp.Console.Services;

/// <summary>
/// Client for registering Temporal workers with the AWA API.
/// Mirrors the Python registration_client.py functionality.
/// </summary>
public class WorkerRegistrationClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<WorkerRegistrationClient> _logger;
    private readonly AwaCoreConfiguration _coreConfiguration;
    private readonly TemporalConfiguration _temporalConfiguration;

    public WorkerRegistrationClient(
        HttpClient httpClient,
        ILogger<WorkerRegistrationClient> logger,
        IOptions<AwaCoreConfiguration> coreConfiguration,
        IOptions<TemporalConfiguration> temporalConfiguration)
    {
        _httpClient = httpClient;
        _logger = logger;
        _coreConfiguration = coreConfiguration.Value;
        _temporalConfiguration = temporalConfiguration.Value;
    }

    /// <summary>
    /// Register worker with the AWA API.
    /// </summary>
    /// <param name="registrationPayload">Dictionary containing worker registration details</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Response data from the API</returns>
    /// <exception cref="HttpRequestException">If the API returns an error status code</exception>
    /// <exception cref="TaskCanceledException">If the request times out</exception>
    public async Task<Dictionary<string, object>?> RegisterWorkerAsync(
        RegistrationPayload registrationPayload,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(_coreConfiguration.ApiBaseUrl))
        {
            throw new InvalidOperationException("AWA API base URL is not configured");
        }

        var url = $"{_coreConfiguration.ApiBaseUrl.TrimEnd('/')}{_coreConfiguration.WorkerRegistrationEndpoint}";

        _logger.LogInformation("Registering worker {WorkerName} v{WorkerVersion} with {WorkflowCount} workflows and {ActivityCount} activities",
            registrationPayload.WorkerName, registrationPayload.WorkerVersion,
            registrationPayload.Workflows.Count, registrationPayload.Activities.Count);

        try
        {
            // Serialize payload to JSON
            var jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                WriteIndented = true
            };
            var jsonPayload = JsonSerializer.Serialize(registrationPayload, jsonOptions);

            _logger.LogDebug("Registration payload: {JsonPayload}", jsonPayload);

            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            // Execute request
            _logger.LogDebug("Sending registration request to: {Url}", url);
            var response = await _httpClient.PostAsync(url, content, cancellationToken);

            // Ensure success status code
            response.EnsureSuccessStatusCode();

            // Parse response
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
            _logger.LogDebug("Registration response: {ResponseContent}", responseContent);

            var responseData = JsonSerializer.Deserialize<Dictionary<string, object>>(responseContent, jsonOptions);

            _logger.LogInformation("Worker registered successfully with AWA API");
            return responseData;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "HTTP error during worker registration to {Url}", url);
            throw new HttpRequestException($"HTTP error during worker registration to {url}: {ex.Message}", ex);
        }
        catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException || ex.CancellationToken.IsCancellationRequested)
        {
            _logger.LogError(ex, "Request timeout during worker registration to {Url}", url);
            throw new TaskCanceledException($"Request timeout during worker registration to {url}", ex);
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to parse JSON response from worker registration API");
            throw new InvalidDataException($"Failed to parse API response from {url}: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// Test connectivity to the AWA API.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>True if the API is reachable, false otherwise</returns>
    public async Task<bool> TestConnectivityAsync(CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(_coreConfiguration.ApiBaseUrl))
        {
            return false;
        }

        try
        {
            var url = $"{_coreConfiguration.ApiBaseUrl.TrimEnd('/')}{_coreConfiguration.HealthEndpoint}";

            _logger.LogDebug("Testing connectivity to AWA API: {Url}", url);

            using var response = await _httpClient.GetAsync(url, cancellationToken);
            var isHealthy = response.IsSuccessStatusCode;

            _logger.LogDebug("AWA API connectivity test result: {IsHealthy}", isHealthy);
            return isHealthy;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to test connectivity to AWA API");
            return false;
        }
    }

    /// <summary>
    /// Register workflows and activities with the AWA API if configured to do so.
    /// </summary>
    /// <param name="workflowInfoList">List of workflows to register</param>
    /// <param name="activityInfoList">List of activities to register</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>True if registration succeeded, false if skipped due to configuration</returns>
    public async Task<bool> RegisterWithApiAsync(
        List<WorkflowInfo> workflowInfoList,
        List<ActivityInfo> activityInfoList,
        CancellationToken cancellationToken = default)
    {
        // Check if registration should be skipped
        if (_coreConfiguration.SkipRegistration)
        {
            _logger.LogInformation("Registration is disabled, skipping API registration");
            return false;
        }

        if (string.IsNullOrWhiteSpace(_coreConfiguration.ApiBaseUrl))
        {
            throw new InvalidOperationException("AWA API base URL must be configured for worker registration");
        }

        _logger.LogInformation("Registering worker with AWA API...");

        try
        {
            // Build registration payload
            var registrationPayload = BuildRegistrationPayload(workflowInfoList, activityInfoList);

            _logger.LogDebug("Registration payload ready: {PayloadJson}",
                System.Text.Json.JsonSerializer.Serialize(registrationPayload,
                    new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));

            // Test connectivity first
            var isConnected = await TestConnectivityAsync(cancellationToken);
            if (!isConnected)
            {
                throw new InvalidOperationException($"AWA API is not reachable at {_coreConfiguration.ApiBaseUrl}. Ensure the AWA Core service is running and accessible.");
            }

            // Register with API
            _logger.LogInformation("Sending registration to AWA API at {ApiUrl}", _coreConfiguration.ApiBaseUrl);
            var response = await RegisterWorkerAsync(registrationPayload, cancellationToken);

            _logger.LogInformation("Worker registered successfully with AWA API. Response: {Response}",
                response != null ? System.Text.Json.JsonSerializer.Serialize(response,
                    new System.Text.Json.JsonSerializerOptions { WriteIndented = true }) : "null");

            return true;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to register worker with AWA API: {ErrorMessage}", ex.Message);
            throw;
        }
    }

    /// <summary>
    /// Build the registration payload for the AWA API.
    /// </summary>
    /// <param name="workflowInfoList">List of workflows to include</param>
    /// <param name="activityInfoList">List of activities to include</param>
    /// <returns>Registration payload ready to send to the API</returns>
    public RegistrationPayload BuildRegistrationPayload(
        List<WorkflowInfo> workflowInfoList,
        List<ActivityInfo> activityInfoList)
    {
        var workflows = workflowInfoList.Select(w => w.ToDict()).ToList();
        var activities = activityInfoList.Select(a => a.ToDict()).ToList();

        var payload = new RegistrationPayload
        {
            WorkerName = _coreConfiguration.WorkerName,
            WorkerVersion = _coreConfiguration.WorkerVersion,
            TaskQueue = _temporalConfiguration.TaskQueue,
            Workflows = workflows,
            Activities = activities
        };

        _logger.LogDebug("Built registration payload: {WorkerName} v{WorkerVersion} with {WorkflowCount} workflows and {ActivityCount} activities",
            payload.WorkerName, payload.WorkerVersion, payload.Workflows.Count, payload.Activities.Count);

        return payload;
    }

    /// <summary>
    /// Get registration details for logging.
    /// </summary>
    /// <param name="workflowInfoList">List of workflows</param>
    /// <param name="activityInfoList">List of activities</param>
    /// <returns>Formatted string with registration details</returns>
    public string GetRegistrationDetails(
        List<WorkflowInfo> workflowInfoList,
        List<ActivityInfo> activityInfoList)
    {
        var details = new List<string>();

        if (workflowInfoList.Count > 0)
        {
            details.Add("Workflows:");
            details.AddRange(workflowInfoList.Select(w => $"  - {w.Name}"));
        }

        if (activityInfoList.Count > 0)
        {
            details.Add("Activities:");
            details.AddRange(activityInfoList.Select(a => $"  - {a.Name}"));
        }

        return string.Join("\n", details);
    }
}
