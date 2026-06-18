namespace AgenticWorkflowApp.Console.Configuration;

/// <summary>
/// Configuration options for AWA Core functionality.
/// </summary>
public class AwaCoreConfiguration
{
    public const string SectionName = "AwaCoreConfiguration";

    /// <summary>
    /// Base URL for the AWA API
    /// </summary>
    public string ApiBaseUrl { get; set; } = "http://localhost:8001";

    /// <summary>
    /// Name of this worker instance
    /// </summary>
    public string WorkerName { get; set; } = "dotnet-worker";

    /// <summary>
    /// Version of this worker instance
    /// </summary>
    public string WorkerVersion { get; set; } = "1.0.0";

    /// <summary>
    /// Whether to enable automatic workflow/activity discovery
    /// </summary>
    public bool EnableAutoDiscovery { get; set; } = true;


    /// <summary>
    /// Whether to skip registration entirely (useful for testing)
    /// </summary>
    public bool SkipRegistration { get; set; } = false;

    /// <summary>
    /// HTTP client timeout in seconds for API calls
    /// </summary>
    public int HttpTimeoutSeconds { get; set; } = 30;

    /// <summary>
    /// Number of retry attempts for failed API calls
    /// </summary>
    public int RetryAttempts { get; set; } = 3;

    /// <summary>
    /// Base delay in milliseconds for retry attempts (uses exponential backoff)
    /// </summary>
    public int RetryDelayMs { get; set; } = 1000;

    /// <summary>
    /// API endpoint path for worker registration (relative to ApiBaseUrl)
    /// </summary>
    public string WorkerRegistrationEndpoint { get; set; } = "/api/v1/workers/register";

    /// <summary>
    /// API endpoint path for health check (relative to ApiBaseUrl)
    /// </summary>
    public string HealthEndpoint { get; set; } = "/api/v1/health";

    /// <summary>
    /// Validate the configuration for consistency and required fields.
    /// </summary>
    /// <exception cref="InvalidOperationException">Thrown when configuration is invalid</exception>
    public void Validate()
    {
        if (EnableAutoDiscovery && string.IsNullOrWhiteSpace(ApiBaseUrl) && !SkipRegistration)
        {
            throw new InvalidOperationException(
                "ApiBaseUrl is required when EnableAutoDiscovery is true and SkipRegistration is false. " +
                "Either provide a valid ApiBaseUrl or set SkipRegistration to true.");
        }

        if (HttpTimeoutSeconds <= 0)
        {
            throw new InvalidOperationException("HttpTimeoutSeconds must be greater than 0");
        }

        if (RetryAttempts < 0)
        {
            throw new InvalidOperationException("RetryAttempts must be non-negative");
        }

        if (RetryDelayMs <= 0)
        {
            throw new InvalidOperationException("RetryDelayMs must be greater than 0");
        }

        if (string.IsNullOrWhiteSpace(WorkerName))
        {
            throw new InvalidOperationException("WorkerName cannot be null or empty");
        }

        if (string.IsNullOrWhiteSpace(WorkerVersion))
        {
            throw new InvalidOperationException("WorkerVersion cannot be null or empty");
        }

        // Validate URI format if provided
        if (!string.IsNullOrWhiteSpace(ApiBaseUrl) && !Uri.TryCreate(ApiBaseUrl, UriKind.Absolute, out _))
        {
            throw new InvalidOperationException($"ApiBaseUrl '{ApiBaseUrl}' is not a valid absolute URI");
        }
    }
}
