using System.Text.Json.Serialization;

namespace AgenticWorkflowApp.Console.Models;

/// <summary>
/// Represents the payload sent to the AWA API for worker registration.
/// Mirrors the Python registration payload structure.
/// </summary>
public record RegistrationPayload
{
    /// <summary>
    /// The name of the worker being registered
    /// </summary>
    [JsonPropertyName("worker_name")]
    public required string WorkerName { get; init; }

    /// <summary>
    /// The version of the worker
    /// </summary>
    [JsonPropertyName("worker_version")]
    public required string WorkerVersion { get; init; }

    /// <summary>
    /// The task queue this worker listens to
    /// </summary>
    [JsonPropertyName("task_queue")]
    public required string TaskQueue { get; init; }

    /// <summary>
    /// List of workflows provided by this worker
    /// </summary>
    [JsonPropertyName("workflows")]
    public List<Dictionary<string, object?>> Workflows { get; init; } = [];

    /// <summary>
    /// List of activities provided by this worker
    /// </summary>
    [JsonPropertyName("activities")]
    public List<Dictionary<string, object?>> Activities { get; init; } = [];
}
