using System.Reflection;
using AgenticWorkflowApp.Console.Services;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace AgenticWorkflowApp.Console.Tests.Services;

public class WorkflowDiscoveryServiceTests
{
    private readonly Mock<ILogger<WorkflowDiscoveryService>> _mockLogger;
    private readonly WorkflowDiscoveryService _discoveryService;

    public WorkflowDiscoveryServiceTests()
    {
        _mockLogger = new Mock<ILogger<WorkflowDiscoveryService>>();
        _discoveryService = new WorkflowDiscoveryService(_mockLogger.Object);
    }

    [Fact]
    public void DiscoverWorkflowsAndActivities_ShouldFindKnownWorkflowsAndActivities()
    {
        // Arrange
        var currentAssembly = Assembly.GetAssembly(typeof(AgenticWorkflowApp.Console.Workflows.HelloWorld.HelloWorldWorkflow));
        var assemblies = new[] { currentAssembly! };

        // Act
        var (workflows, activities) = _discoveryService.DiscoverWorkflowsAndActivities(assemblies);

        // Assert
        var workflowList = workflows.ToList();
        var activityList = activities.ToList();

        Assert.NotEmpty(workflowList);
        Assert.NotEmpty(activityList);

        // Should find HelloWorldWorkflow
        Assert.Contains(workflowList, w => w.Name == "HelloWorldWorkflow");

        // Should find our known activities
        Assert.Contains(activityList, a => a.Name == "Run" && a.DeclaringType?.Name == "AddTimestampActivity");
        Assert.Contains(activityList, a => a.Name == "Run" && a.DeclaringType?.Name == "GetHeaderActivity");
    }

    [Fact]
    public void IsWorkflowClass_ShouldReturnTrue_ForWorkflowClass()
    {
        // Arrange
        var workflowType = typeof(AgenticWorkflowApp.Console.Workflows.HelloWorld.HelloWorldWorkflow);

        // Act
        var result = WorkflowDiscoveryService.IsWorkflowClass(workflowType);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsWorkflowClass_ShouldReturnFalse_ForNonWorkflowClass()
    {
        // Arrange
        var nonWorkflowType = typeof(string);

        // Act
        var result = WorkflowDiscoveryService.IsWorkflowClass(nonWorkflowType);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void IsActivityMethod_ShouldReturnTrue_ForActivityMethod()
    {
        // Arrange
        var activityType = typeof(AgenticWorkflowApp.Console.Workflows.HelloWorld.Activities.AddTimestampActivity);
        var runMethod = activityType.GetMethod("Run");

        // Act
        var result = WorkflowDiscoveryService.IsActivityMethod(runMethod!);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsActivityMethod_ShouldReturnFalse_ForNonActivityMethod()
    {
        // Arrange
        var stringType = typeof(string);
        var toStringMethod = stringType.GetMethod("ToString", Array.Empty<Type>());

        // Act
        var result = WorkflowDiscoveryService.IsActivityMethod(toStringMethod!);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void GetWorkflowRunMethod_ShouldReturnRunMethod_ForWorkflowClass()
    {
        // Arrange
        var workflowType = typeof(AgenticWorkflowApp.Console.Workflows.HelloWorld.HelloWorldWorkflow);

        // Act
        var runMethod = WorkflowDiscoveryService.GetWorkflowRunMethod(workflowType);

        // Assert
        Assert.NotNull(runMethod);
        Assert.Equal("RunAsync", runMethod.Name);
    }

    [Fact]
    public void GetDefaultAssembliesToScan_ShouldReturnAssemblies()
    {
        // Act
        var assemblies = WorkflowDiscoveryService.GetDefaultAssembliesToScan();

        // Assert
        Assert.NotEmpty(assemblies);
        // Should include assemblies (the exact ones depend on the execution context)
        Assert.True(assemblies.Length > 0);
    }
}
