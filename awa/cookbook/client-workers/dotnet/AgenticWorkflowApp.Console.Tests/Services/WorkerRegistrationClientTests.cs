using System.Net;
using System.Text.Json;
using AgenticWorkflowApp.Console.Configuration;
using AgenticWorkflowApp.Console.Models;
using AgenticWorkflowApp.Console.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Moq;
using Moq.Protected;
using Xunit;

namespace AgenticWorkflowApp.Console.Tests.Services;

public class WorkerRegistrationClientTests : IDisposable
{
    private readonly Mock<ILogger<WorkerRegistrationClient>> _mockLogger;
    private readonly Mock<HttpMessageHandler> _mockHttpHandler;
    private readonly HttpClient _httpClient;
    private readonly AwaCoreConfiguration _coreConfig;
    private readonly TemporalConfiguration _temporalConfig;
    private readonly WorkerRegistrationClient _client;

    public WorkerRegistrationClientTests()
    {
        _mockLogger = new Mock<ILogger<WorkerRegistrationClient>>();
        _mockHttpHandler = new Mock<HttpMessageHandler>();
        _httpClient = new HttpClient(_mockHttpHandler.Object);

        _coreConfig = new AwaCoreConfiguration
        {
            ApiBaseUrl = "http://localhost:8001",
            WorkerName = "test-worker",
            WorkerVersion = "1.0.0"
        };

        _temporalConfig = new TemporalConfiguration
        {
            TaskQueue = "test-queue"
        };

        var mockCoreOptions = new Mock<IOptions<AwaCoreConfiguration>>();
        mockCoreOptions.Setup(x => x.Value).Returns(_coreConfig);

        var mockTemporalOptions = new Mock<IOptions<TemporalConfiguration>>();
        mockTemporalOptions.Setup(x => x.Value).Returns(_temporalConfig);

        _client = new WorkerRegistrationClient(_httpClient, _mockLogger.Object, mockCoreOptions.Object, mockTemporalOptions.Object);
    }

    [Fact]
    public async Task RegisterWorkerAsync_WithValidPayload_ShouldReturnResponse()
    {
        // Arrange
        var payload = new RegistrationPayload
        {
            WorkerName = "test-worker",
            WorkerVersion = "1.0.0",
            TaskQueue = "test-queue",
            Workflows = new List<Dictionary<string, object?>>(),
            Activities = new List<Dictionary<string, object?>>()
        };

        var expectedResponse = new Dictionary<string, object> { ["status"] = "success" };
        var responseJson = JsonSerializer.Serialize(expectedResponse);

        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent(responseJson)
            });

        // Act
        var result = await _client.RegisterWorkerAsync(payload);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("success", result["status"]?.ToString());
    }

    [Fact]
    public async Task RegisterWorkerAsync_WithHttpError_ShouldThrowHttpRequestException()
    {
        // Arrange
        var payload = new RegistrationPayload
        {
            WorkerName = "test-worker",
            WorkerVersion = "1.0.0",
            TaskQueue = "test-queue",
            Workflows = new List<Dictionary<string, object?>>(),
            Activities = new List<Dictionary<string, object?>>()
        };

        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.BadRequest,
                Content = new StringContent("Bad Request")
            });

        // Act & Assert
        await Assert.ThrowsAsync<HttpRequestException>(() => _client.RegisterWorkerAsync(payload));
    }

    [Fact]
    public async Task TestConnectivityAsync_WithHealthyApi_ShouldReturnTrue()
    {
        // Arrange
        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK
            });

        // Act
        var result = await _client.TestConnectivityAsync();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public async Task RegisterWorkerAsync_WithCustomEndpoints_ShouldUseConfiguredPaths()
    {
        // Arrange
        _coreConfig.WorkerRegistrationEndpoint = "/custom/api/register";
        var payload = new RegistrationPayload
        {
            WorkerName = "test-worker",
            WorkerVersion = "1.0.0",
            TaskQueue = "test-queue",
            Workflows = new List<Dictionary<string, object?>>(),
            Activities = new List<Dictionary<string, object?>>()
        };

        var expectedResponse = new Dictionary<string, object> { ["status"] = "success" };
        var responseJson = JsonSerializer.Serialize(expectedResponse);

        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.Is<HttpRequestMessage>(req => req.RequestUri!.ToString().Contains("/custom/api/register")),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent(responseJson)
            });

        // Act
        var result = await _client.RegisterWorkerAsync(payload);

        // Assert
        Assert.NotNull(result);
        _mockHttpHandler.Protected().Verify(
            "SendAsync",
            Times.Once(),
            ItExpr.Is<HttpRequestMessage>(req => req.RequestUri!.ToString().Contains("/custom/api/register")),
            ItExpr.IsAny<CancellationToken>()
        );
    }

    [Fact]
    public async Task TestConnectivityAsync_WithCustomHealthEndpoint_ShouldUseConfiguredPath()
    {
        // Arrange
        _coreConfig.HealthEndpoint = "/custom/health/check";

        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.Is<HttpRequestMessage>(req => req.RequestUri!.ToString().Contains("/custom/health/check")),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK
            });

        // Act
        var result = await _client.TestConnectivityAsync();

        // Assert
        Assert.True(result);
        _mockHttpHandler.Protected().Verify(
            "SendAsync",
            Times.Once(),
            ItExpr.Is<HttpRequestMessage>(req => req.RequestUri!.ToString().Contains("/custom/health/check")),
            ItExpr.IsAny<CancellationToken>()
        );
    }

    [Fact]
    public async Task TestConnectivityAsync_WithUnhealthyApi_ShouldReturnFalse()
    {
        // Arrange
        _mockHttpHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.ServiceUnavailable
            });

        // Act
        var result = await _client.TestConnectivityAsync();

        // Assert
        Assert.False(result);
    }

    [Fact]
    public async Task RegisterWorkerAsync_WithEmptyApiBaseUrl_ShouldThrowInvalidOperationException()
    {
        // Arrange
        _coreConfig.ApiBaseUrl = "";
        var payload = new RegistrationPayload
        {
            WorkerName = "test-worker",
            WorkerVersion = "1.0.0",
            TaskQueue = "test-queue",
            Workflows = new List<Dictionary<string, object?>>(),
            Activities = new List<Dictionary<string, object?>>()
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => _client.RegisterWorkerAsync(payload));
    }

    public void Dispose()
    {
        _httpClient.Dispose();
    }
}
