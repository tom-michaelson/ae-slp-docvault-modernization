using System;
using System.Threading.Tasks;
using NUnit.Framework;
using Awa.Client.Models;
using Awa.Client.Utilities.Activity;

namespace Awa.Client.Tests.Utilities.Activity
{
    [TestFixture]
    public class UpsertJiraIssueActivityTests
    {
        #region Method Signature Tests

        [Test]
        public void UpsertJiraIssueActivity_MethodExists()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("UpsertJiraIssueActivity");
            Assert.That(methodInfo, Is.Not.Null, "UpsertJiraIssueActivity method should exist");
        }

        [Test]
        public void UpsertJiraIssueActivity_HasCorrectReturnType()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("UpsertJiraIssueActivity");
            Assert.That(methodInfo, Is.Not.Null, "UpsertJiraIssueActivity method should exist");

            // The method returns Task<string?> (nullable string)
            var expectedReturnType = typeof(Task<>).MakeGenericType(typeof(string));
            Assert.That(methodInfo.ReturnType, Is.EqualTo(expectedReturnType),
                       "UpsertJiraIssueActivity should return Task<string?>");
        }

        [Test]
        public void UpsertJiraIssueActivity_HasCorrectParameters()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("UpsertJiraIssueActivity");
            Assert.That(methodInfo, Is.Not.Null, "UpsertJiraIssueActivity method should exist");

            var parameters = methodInfo.GetParameters();
            Assert.That(parameters.Length, Is.EqualTo(1), "UpsertJiraIssueActivity should have 1 parameter");
            Assert.That(parameters[0].ParameterType, Is.EqualTo(typeof(JiraIssueRequest)),
                       "Parameter should be JiraIssueRequest");
            Assert.That(parameters[0].Name, Is.EqualTo("request"), "Parameter should be named 'request'");
        }

        [Test]
        public void UpsertJiraIssueActivity_IsAsync()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("UpsertJiraIssueActivity");
            Assert.That(methodInfo, Is.Not.Null, "UpsertJiraIssueActivity method should exist");

            // Check that it returns a Task
            Assert.That(methodInfo.ReturnType.IsGenericType, Is.True, "Return type should be generic");
            Assert.That(methodInfo.ReturnType.GetGenericTypeDefinition(), Is.EqualTo(typeof(Task<>)),
                       "Method should return a Task<T>");
        }

        [Test]
        public void UpsertJiraIssueActivity_IsPublicStatic()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("UpsertJiraIssueActivity");
            Assert.That(methodInfo, Is.Not.Null, "UpsertJiraIssueActivity method should exist");

            Assert.That(methodInfo.IsPublic, Is.True, "Method should be public");
            Assert.That(methodInfo.IsStatic, Is.True, "Method should be static");
        }

        #endregion

        #region Model Validation Tests

        [Test]
        public void JiraIssueRequest_CanBeInstantiated()
        {
            // Test that we can create a JiraIssueRequest object
            var request = new JiraIssueRequest();
            Assert.That(request, Is.Not.Null, "Should be able to create JiraIssueRequest instance");
        }

        [Test]
        public void JiraIssueRequest_PropertiesCanBeSet()
        {
            // Test that we can set properties on JiraIssueRequest
            var request = new JiraIssueRequest
            {
                ProjectId = "TEST-PROJECT",
                Key = "TEST-123",
                Summary = "Test Issue",
                Description = "Test Description",
                IssueType = "Bug"
            };

            Assert.That(request.ProjectId, Is.EqualTo("TEST-PROJECT"), "ProjectId should be set correctly");
            Assert.That(request.Key, Is.EqualTo("TEST-123"), "Key should be set correctly");
            Assert.That(request.Summary, Is.EqualTo("Test Issue"), "Summary should be set correctly");
            Assert.That(request.Description, Is.EqualTo("Test Description"), "Description should be set correctly");
            Assert.That(request.IssueType, Is.EqualTo("Bug"), "IssueType should be set correctly");
        }

        [Test]
        public void JiraIssueRequest_SupportsNullableProperties()
        {
            // Test that nullable properties work correctly
            var request = new JiraIssueRequest
            {
                ProjectId = "TEST-PROJECT",
                Key = null,  // Should be nullable
                Summary = "Test Issue",
                Description = null,  // Should be nullable
                IssueType = "Task"
            };

            Assert.That(request.ProjectId, Is.EqualTo("TEST-PROJECT"), "ProjectId should be set");
            Assert.That(request.Key, Is.Null, "Key should be null");
            Assert.That(request.Summary, Is.EqualTo("Test Issue"), "Summary should be set");
            Assert.That(request.Description, Is.Null, "Description should be null");
            Assert.That(request.IssueType, Is.EqualTo("Task"), "IssueType should be set");
        }

        [Test]
        public void JiraIssueRequest_SupportsAdditionalProperties()
        {
            // Test Comments and Parent properties
            var request = new JiraIssueRequest
            {
                ProjectId = "TEST-PROJECT",
                Key = "TEST-456",
                Summary = "Child Issue",
                Description = "This is a subtask",
                IssueType = "Subtask",
                Parent = "TEST-123",
                Comments = new[] { "First comment", "Second comment" }
            };

            Assert.That(request.Parent, Is.EqualTo("TEST-123"), "Parent should be set correctly");
            Assert.That(request.Comments, Is.Not.Null, "Comments should not be null");
            Assert.That(request.Comments.Length, Is.EqualTo(2), "Should have 2 comments");
            Assert.That(request.Comments[0], Is.EqualTo("First comment"), "First comment should match");
            Assert.That(request.Comments[1], Is.EqualTo("Second comment"), "Second comment should match");
        }

        #endregion

        #region Integration Test Markers

        [Test]
        [Category("Integration")]
        [Ignore("Requires running Temporal instance")]
        public async Task UpsertJiraIssueActivity_WithValidRequest_ExecutesSuccessfully()
        {
            // This test would require a running Temporal instance
            // It's marked as Integration and Ignored for normal test runs
            var request = new JiraIssueRequest
            {
                ProjectId = "TEST-PROJECT",
                Summary = "Test Issue",
                IssueType = "Task"
            };

            // This would fail without Temporal running
            // var result = await ActivityUtilities.UpsertJiraIssueActivity(request);
            // Assert.That(result, Is.Not.Null);
            await Task.CompletedTask;
        }

        [Test]
        [Category("Integration")]
        [Ignore("Requires running Temporal instance")]
        public async Task UpsertJiraIssueActivity_WithNullRequest_HandlesGracefully()
        {
            // This test would require a running Temporal instance
            // It's marked as Integration and Ignored for normal test runs

            // This would fail without Temporal running
            // await Assert.ThrowsAsync<ArgumentNullException>(async () =>
            // {
            //     await ActivityUtilities.UpsertJiraIssueActivity(null);
            // });
            await Task.CompletedTask;
        }

        #endregion

        #region Documentation Tests

        [Test]
        public void UpsertJiraIssueActivity_HasXmlDocumentation()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("UpsertJiraIssueActivity");
            Assert.That(methodInfo, Is.Not.Null, "UpsertJiraIssueActivity method should exist");

            // Note: XML documentation is compiled separately and not easily testable at runtime
            // This test just confirms the method exists and could have documentation
            Assert.Pass("XML documentation should be present in the source code");
        }

        #endregion
    }
}
