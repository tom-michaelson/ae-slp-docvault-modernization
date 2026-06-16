namespace AgenticWorkflowApp.Console.Models;

/// <summary>
/// Information about a discovered workflow.
/// Inherits from TemporalInfo and adds workflow-specific attributes.
/// </summary>
public record WorkflowInfo : TemporalInfo
{
    /// <summary>
    /// The C# class name of the workflow
    /// </summary>
    public required string ClassName { get; init; }

    /// <summary>
    /// The C# type of the workflow class
    /// </summary>
    public required Type WorkflowType { get; init; }
}
