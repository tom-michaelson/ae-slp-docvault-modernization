namespace AgenticWorkflowApp.Console.Models;

/// <summary>
/// Contains information about a workflow or activity parameter.
/// Mirrors the Python ParameterInfo class structure.
/// </summary>
public record ParameterInfo
{
    /// <summary>
    /// The parameter name
    /// </summary>
    public required string Name { get; init; }

    /// <summary>
    /// String representation of the parameter type
    /// </summary>
    public string? TypeString { get; init; }

    /// <summary>
    /// The actual C# Type of the parameter
    /// </summary>
    public Type? ParameterType { get; init; }
}
