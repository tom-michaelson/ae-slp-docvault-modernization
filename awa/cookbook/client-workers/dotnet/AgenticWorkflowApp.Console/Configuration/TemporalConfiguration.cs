namespace AgenticWorkflowApp.Console.Configuration;

/// <summary>
/// Configuration options for Temporal client and worker settings.
/// </summary>
public class TemporalConfiguration
{
    public const string SectionName = "Temporal";

    /// <summary>
    /// Temporal server target host (e.g., localhost:7233)
    /// </summary>
    public string ClientTargetHost { get; set; } = "localhost:7233";

    /// <summary>
    /// Temporal namespace to use
    /// </summary>
    public string ClientNamespace { get; set; } = "default";

    /// <summary>
    /// Task queue for this worker to listen on
    /// </summary>
    public string TaskQueue { get; set; } = "awa_client_dotnet";
}
