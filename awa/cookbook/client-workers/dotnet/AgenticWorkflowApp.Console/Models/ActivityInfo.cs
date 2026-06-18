using System.Reflection;

namespace AgenticWorkflowApp.Console.Models;

/// <summary>
/// Information about a discovered activity.
/// Inherits from TemporalInfo and adds activity-specific attributes.
/// </summary>
public record ActivityInfo : TemporalInfo
{
    /// <summary>
    /// The C# method name of the activity
    /// </summary>
    public required string MethodName { get; init; }

    /// <summary>
    /// The C# class name containing the activity method
    /// </summary>
    public required string ClassName { get; init; }

    /// <summary>
    /// The MethodInfo for the activity method
    /// </summary>
    public required MethodInfo Method { get; init; }
}
