using System.Text.Json.Serialization;

namespace AgenticWorkflowApp.Console.Models;

/// <summary>
/// Base class for Temporal workflow and activity information.
/// Mirrors the Python TemporalInfo base class structure.
/// </summary>
public abstract record TemporalInfo
{
    /// <summary>
    /// The name of the workflow/activity as defined in the attribute
    /// </summary>
    public required string Name { get; init; }

    /// <summary>
    /// The module where the workflow/activity is defined (assembly + namespace)
    /// </summary>
    public required string Module { get; init; }

    /// <summary>
    /// JSON schema representation of the input parameters
    /// </summary>
    public required object Parameters { get; init; }

    /// <summary>
    /// List of task queues this workflow/activity is registered to
    /// </summary>
    public List<string> Queues { get; init; } = [];

    /// <summary>
    /// Convert to dictionary format expected by AWA API
    /// </summary>
    /// <returns>Dictionary with name, task_queue, and input_schema</returns>
    public Dictionary<string, object?> ToDict()
    {
        return new Dictionary<string, object?>
        {
            ["name"] = Name,
            ["task_queue"] = Queues.FirstOrDefault(),
            ["input_schema"] = Parameters
        };
    }
}
