using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Awa.Client.Utilities.Workflow;
using NUnit.Framework;

namespace Awa.Client.Tests.Utilities.Workflow
{
    [TestFixture]
    public class RunWithControlledConcurrencyWorkflowTests
    {
        [Test]
        public async Task RunWithControlledConcurrency_WithEmptyList_ReturnsEmptyList()
        {
            // Arrange
            var coroutineFuncs = new List<Func<Task<object?>>>();
            int maxConcurrency = 3;

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(0, result.Count);
        }

        [Test]
        public async Task RunWithControlledConcurrency_WithNullList_ReturnsEmptyList()
        {
            // Arrange
            List<Func<Task<object?>>>? coroutineFuncs = null;
            int maxConcurrency = 3;

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs!, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(0, result.Count);
        }

        [Test]
        public async Task RunWithControlledConcurrency_WithSingleTask_ReturnsCorrectResult()
        {
            // Arrange
            var expectedResult = "test result";
            var coroutineFuncs = new List<Func<Task<object?>>>
            {
                async () =>
                {
                    await Task.Delay(10);
                    return expectedResult;
                }
            };
            int maxConcurrency = 1;

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(1, result.Count);
            Assert.AreEqual(expectedResult, result[0]);
        }

        [Test]
        public async Task RunWithControlledConcurrency_WithMultipleTasks_ReturnsResultsInOrder()
        {
            // Arrange
            var coroutineFuncs = new List<Func<Task<object?>>>
            {
                async () =>
                {
                    await Task.Delay(50);
                    return "first";
                },
                async () =>
                {
                    await Task.Delay(10);
                    return "second";
                },
                async () =>
                {
                    await Task.Delay(30);
                    return "third";
                }
            };
            int maxConcurrency = 3;

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(3, result.Count);
            Assert.AreEqual("first", result[0]);
            Assert.AreEqual("second", result[1]);
            Assert.AreEqual("third", result[2]);
        }

        [Test]
        public async Task RunWithControlledConcurrency_LimitsConcurrency()
        {
            // Arrange
            int maxConcurrency = 2;
            int activeCount = 0;
            int maxActiveCount = 0;
            var lockObj = new object();

            var coroutineFuncs = new List<Func<Task<object?>>>();
            for (int i = 0; i < 5; i++)
            {
                int taskId = i;
                coroutineFuncs.Add(async () =>
                {
                    lock (lockObj)
                    {
                        activeCount++;
                        if (activeCount > maxActiveCount)
                        {
                            maxActiveCount = activeCount;
                        }
                    }

                    await Task.Delay(50); // Simulate work

                    lock (lockObj)
                    {
                        activeCount--;
                    }

                    return $"Task {taskId}";
                });
            }

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(5, result.Count);
            Assert.LessOrEqual(maxActiveCount, maxConcurrency,
                $"Maximum active tasks ({maxActiveCount}) exceeded concurrency limit ({maxConcurrency})");

            // Verify all tasks completed and returned in order
            for (int i = 0; i < 5; i++)
            {
                Assert.AreEqual($"Task {i}", result[i]);
            }
        }

        [Test]
        public async Task RunWithControlledConcurrency_WithHigherConcurrencyThanTasks_UsesTaskCount()
        {
            // Arrange
            int maxConcurrency = 10;
            int taskCount = 3;
            int activeCount = 0;
            int maxActiveCount = 0;
            var lockObj = new object();

            var coroutineFuncs = new List<Func<Task<object?>>>();
            for (int i = 0; i < taskCount; i++)
            {
                int taskId = i;
                coroutineFuncs.Add(async () =>
                {
                    lock (lockObj)
                    {
                        activeCount++;
                        if (activeCount > maxActiveCount)
                        {
                            maxActiveCount = activeCount;
                        }
                    }

                    await Task.Delay(50); // Simulate work

                    lock (lockObj)
                    {
                        activeCount--;
                    }

                    return $"Task {taskId}";
                });
            }

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(taskCount, result.Count);
            Assert.LessOrEqual(maxActiveCount, taskCount,
                $"Maximum active tasks ({maxActiveCount}) should not exceed task count ({taskCount})");
        }

        [Test]
        public async Task RunWithControlledConcurrency_WithExceptionInTask_PropagatesException()
        {
            // Arrange
            var coroutineFuncs = new List<Func<Task<object?>>>
            {
                async () =>
                {
                    await Task.Delay(10);
                    return "success";
                },
                async () =>
                {
                    await Task.Delay(20);
                    throw new InvalidOperationException("Test exception");
                },
                async () =>
                {
                    await Task.Delay(10);
                    return "another success";
                }
            };
            int maxConcurrency = 2;

            // Act & Assert
            Assert.ThrowsAsync<InvalidOperationException>(async () =>
            {
                await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);
            });
        }

        [Test]
        public async Task RunWithControlledConcurrency_WithNullResults_HandlesCorrectly()
        {
            // Arrange
            var coroutineFuncs = new List<Func<Task<object?>>>
            {
                async () =>
                {
                    await Task.Delay(10);
                    return null;
                },
                async () =>
                {
                    await Task.Delay(10);
                    return "not null";
                },
                async () =>
                {
                    await Task.Delay(10);
                    return null;
                }
            };
            int maxConcurrency = 2;

            // Act
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(3, result.Count);
            Assert.IsNull(result[0]);
            Assert.AreEqual("not null", result[1]);
            Assert.IsNull(result[2]);
        }

        [Test]
        public async Task RunWithControlledConcurrency_PerformanceTest_MaintainsConcurrency()
        {
            // Arrange
            int maxConcurrency = 3;
            int taskCount = 10;
            var taskDelayMs = 100;
            var stopwatch = new Stopwatch();

            var coroutineFuncs = new List<Func<Task<object?>>>();
            for (int i = 0; i < taskCount; i++)
            {
                int taskId = i;
                coroutineFuncs.Add(async () =>
                {
                    await Task.Delay(taskDelayMs);
                    return taskId;
                });
            }

            // Act
            stopwatch.Start();
            var result = await WorkflowUtilities.RunWithControlledConcurrencyWorkflow(coroutineFuncs, maxConcurrency);
            stopwatch.Stop();

            // Assert
            Assert.IsNotNull(result);
            Assert.AreEqual(taskCount, result.Count);

            // With proper concurrency control, total time should be approximately:
            // (taskCount / maxConcurrency) * taskDelayMs
            // We'll allow some tolerance for overhead
            var expectedMinTime = (taskCount / maxConcurrency) * taskDelayMs;
            var expectedMaxTime = expectedMinTime + (2 * taskDelayMs); // Allow for overhead

            Assert.GreaterOrEqual(stopwatch.ElapsedMilliseconds, expectedMinTime - 50,
                $"Execution was too fast, suggesting concurrency wasn't limited properly");
            Assert.LessOrEqual(stopwatch.ElapsedMilliseconds, expectedMaxTime + 100,
                $"Execution was too slow, suggesting inefficient concurrency management");

            // Verify results are in order
            for (int i = 0; i < taskCount; i++)
            {
                Assert.AreEqual(i, result[i]);
            }
        }
    }
}
