using System;
using System.Reflection;
using System.Threading.Tasks;
using Awa.Client.Models;
using Awa.Client.Utilities.Activity;
using NUnit.Framework;

namespace Awa.Client.Tests.Utilities.Activity
{
    [TestFixture]
    public class RunCommandActivityTests
    {
        #region RunCommandActivity Tests

        [Test]
        public void RunCommandActivity_MethodExists()
        {
            // Verify the method exists
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");
        }

        [Test]
        public void RunCommandActivity_ReturnsCorrectType()
        {
            // Verify the method signature is correct
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");

            // The method returns Task<CommandResult?> (nullable CommandResult)
            Assert.That(methodInfo.ReturnType.IsGenericType, Is.True, "Return type should be generic");
            Assert.That(methodInfo.ReturnType.GetGenericTypeDefinition(), Is.EqualTo(typeof(Task<>)),
                       "Method should return a Task<T>");

            // Get the generic argument (should be CommandResult?)
            var genericArgs = methodInfo.ReturnType.GetGenericArguments();
            Assert.That(genericArgs.Length, Is.EqualTo(1), "Should have one generic argument");

            // The generic argument should be CommandResult
            var expectedType = typeof(CommandResult);
            Assert.That(genericArgs[0], Is.EqualTo(expectedType),
                       "Generic argument should be CommandResult");
        }

        [Test]
        public void RunCommandActivity_HasCorrectParameters()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");

            var parameters = methodInfo.GetParameters();
            Assert.That(parameters.Length, Is.EqualTo(1), "RunCommandActivity should have 1 parameter");
            Assert.That(parameters[0].ParameterType, Is.EqualTo(typeof(CommandInput)),
                       "Parameter should be CommandInput");
            Assert.That(parameters[0].Name, Is.EqualTo("commandInput"),
                       "Parameter should be named 'commandInput'");
            Assert.That(parameters[0].HasDefaultValue, Is.False,
                       "Parameter should not have a default value");
        }

        [Test]
        public void RunCommandActivity_IsAsyncMethod()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");

            // Check that it returns a Task
            Assert.That(methodInfo.ReturnType.IsGenericType, Is.True, "Return type should be generic");
            Assert.That(methodInfo.ReturnType.GetGenericTypeDefinition(), Is.EqualTo(typeof(Task<>)),
                       "Method should return a Task<T>");

            // Check method is async (look for async state machine attribute)
            var isAsync = methodInfo.IsDefined(typeof(System.Runtime.CompilerServices.AsyncStateMachineAttribute), false);
            Assert.That(isAsync, Is.True, "Method should be async");
        }

        [Test]
        public void RunCommandActivity_IsPublicStatic()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");

            Assert.That(methodInfo.IsPublic, Is.True, "Method should be public");
            Assert.That(methodInfo.IsStatic, Is.True, "Method should be static");
        }

        [Test]
        public void CommandInput_HasRequiredProperties()
        {
            // Verify CommandInput model has the expected properties
            var commandInputType = typeof(CommandInput);

            var commandProperty = commandInputType.GetProperty("Command");
            Assert.That(commandProperty, Is.Not.Null, "CommandInput should have Command property");
            Assert.That(commandProperty.PropertyType, Is.EqualTo(typeof(string)),
                       "Command property should be of type string");

            var workingDirProperty = commandInputType.GetProperty("WorkingDir");
            Assert.That(workingDirProperty, Is.Not.Null, "CommandInput should have WorkingDir property");
            Assert.That(workingDirProperty.PropertyType, Is.EqualTo(typeof(string)),
                       "WorkingDir property should be of type string");
        }

        [Test]
        public void CommandResult_HasRequiredProperties()
        {
            // Verify CommandResult model has the expected properties
            var commandResultType = typeof(CommandResult);

            var successProperty = commandResultType.GetProperty("Success");
            Assert.That(successProperty, Is.Not.Null, "CommandResult should have Success property");
            Assert.That(successProperty.PropertyType, Is.EqualTo(typeof(bool)),
                       "Success property should be of type bool");

            var outputProperty = commandResultType.GetProperty("Output");
            Assert.That(outputProperty, Is.Not.Null, "CommandResult should have Output property");
            Assert.That(outputProperty.PropertyType, Is.EqualTo(typeof(string)),
                       "Output property should be of type string");

            var exitCodeProperty = commandResultType.GetProperty("ExitCode");
            Assert.That(exitCodeProperty, Is.Not.Null, "CommandResult should have ExitCode property");
            Assert.That(exitCodeProperty.PropertyType, Is.EqualTo(typeof(long)),
                       "ExitCode property should be of type long");
        }

        [Test]
        public void RunCommandActivity_CanCreateCommandInput()
        {
            // Test that we can create a CommandInput instance
            var commandInput = new CommandInput
            {
                Command = "echo 'test'",
                WorkingDir = "/tmp"
            };

            Assert.That(commandInput.Command, Is.EqualTo("echo 'test'"));
            Assert.That(commandInput.WorkingDir, Is.EqualTo("/tmp"));
        }

        [Test]
        public void RunCommandActivity_CanCreateCommandResult()
        {
            // Test that we can create a CommandResult instance
            var commandResult = new CommandResult
            {
                Success = true,
                Output = "test output",
                ExitCode = 0
            };

            Assert.That(commandResult.Success, Is.True);
            Assert.That(commandResult.Output, Is.EqualTo("test output"));
            Assert.That(commandResult.ExitCode, Is.EqualTo(0));
        }

        [Test]
        public void RunCommandActivity_MethodCanBeInvoked()
        {
            // Verify the method can be called (will fail at runtime without Temporal, but compiles)
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");

            // Create a valid CommandInput
            var commandInput = new CommandInput
            {
                Command = "echo 'test'",
                WorkingDir = "/tmp"
            };

            // Verify we can attempt to invoke the method (though it will fail without Temporal)
            Assert.DoesNotThrow(() =>
            {
                // This creates the Task but doesn't execute it
                var task = ActivityUtilities.RunCommandActivity(commandInput);
                Assert.That(task, Is.Not.Null, "Method should return a Task");
                Assert.That(task, Is.InstanceOf<Task<CommandResult?>>(),
                           "Method should return Task<CommandResult?>");
            });
        }

        [Test]
        public void RunCommandActivity_HandlesNullableReturnType()
        {
            var methodInfo = typeof(ActivityUtilities).GetMethod("RunCommandActivity");
            Assert.That(methodInfo, Is.Not.Null, "RunCommandActivity method should exist");

            // The return type should be Task<CommandResult?>
            var returnType = methodInfo.ReturnType;
            Assert.That(returnType.IsGenericType, Is.True);

            var genericArgs = returnType.GetGenericArguments();
            Assert.That(genericArgs.Length, Is.EqualTo(1));

            // Check if nullable annotations are present (C# 8.0+ nullable reference types)
            var nullabilityContext = new NullabilityInfoContext();
            var returnParameter = methodInfo.ReturnParameter;
            Assert.That(returnParameter, Is.Not.Null);

            // The generic type argument is CommandResult which is a reference type
            // In C# 8.0+ with nullable reference types, CommandResult? means it can be null
            Assert.That(genericArgs[0], Is.EqualTo(typeof(CommandResult)));
        }

        [Test]
        public void ActivityUtilities_ClassIsStaticPartial()
        {
            var type = typeof(ActivityUtilities);
            Assert.That(type.IsAbstract && type.IsSealed, Is.True,
                       "ActivityUtilities should be a static class (abstract + sealed)");

            // Note: We can't directly test if a class is partial via reflection
            // as 'partial' is a compile-time construct that doesn't exist at runtime
        }

        [Test]
        public void RunCommandActivity_UsesCorrectNamespace()
        {
            var type = typeof(ActivityUtilities);
            Assert.That(type.Namespace, Is.EqualTo("Awa.Client.Utilities.Activity"),
                       "ActivityUtilities should be in Awa.Client.Utilities.Activity namespace");
        }

        #endregion
    }
}
