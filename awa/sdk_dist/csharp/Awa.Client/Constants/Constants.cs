using System;

namespace Awa.Client.Constants
{
    /// <summary>
    /// Constants used throughout the AWA SDK for task queues, timeouts, activity names, and workflow names.
    /// </summary>
    public static class AwaConstants
    {
        // Task Queue
        public const string AwaDefaultTaskQueue = "awa_default";

        // Timeouts (in seconds)
        public const int FileIoTimeoutSeconds = 30;
        public const int AgentTimeoutSeconds = 900; // 15 minutes
        public const int BamlTimeoutSeconds = 60 * 15; // 2 minutes
        public const int McpTimeoutSeconds = 30;
        public const int GitTimeoutSeconds = 300; // 5 minutes
        public const int DefaultBamlActivityTimeoutSeconds = 60 * 15;

        // Activity Names
        public const string AwaPrefix = "awa-";

        public const string ActivitySayHello = AwaPrefix + "say-hello";
        public const string ActivityIsDirectory = AwaPrefix + "is-directory";
        public const string ActivityReadFile = AwaPrefix + "read-file";
        public const string ActivityReadFileAndParse = AwaPrefix + "read-file-and-parse";
        public const string ActivityReadFileBytes = AwaPrefix + "read-file-bytes";
        public const string ActivityReadFileOrDirectory = AwaPrefix + "read-file-or-directory";
        public const string ActivityWriteFile = AwaPrefix + "write-file";
        public const string ActivityCopyFile = AwaPrefix + "copy-file";
        public const string ActivityCopyDirectory = AwaPrefix + "copy-directory";
        public const string ActivityDeleteDirectory = AwaPrefix + "delete-directory";
        public const string ActivityListDirectory = AwaPrefix + "list-directory";
        public const string ActivityReadDirectory = AwaPrefix + "read-directory";
        public const string ActivityListAllDirectoriesRecursive = AwaPrefix + "list-all-directories-recursive";
        public const string ActivityGetDirectoryInfo = AwaPrefix + "get-directory-info";
        public const string ActivityExecuteAgent = AwaPrefix + "execute-agent";
        public const string ActivityExecuteAgentStreaming = AwaPrefix + "execute-agent-streaming";
        public const string ActivityTransform = AwaPrefix + "transform";
        public const string ActivityGenerateBamlClient = AwaPrefix + "generate-baml-client";
        public const string ActivityInvokeMcpTool = AwaPrefix + "invoke-mcp-tool";
        public const string ActivityResolveTemplate = AwaPrefix + "resolve-template";
        public const string ActivityApplyDiff = AwaPrefix + "apply-diff";
        public const string ActivityParseSchema = AwaPrefix + "parse-schema";
        public const string ActivitySetupIsolatedAgent = AwaPrefix + "setup-isolated-agent";
        public const string ActivitySetupIsolatedAgentGit = AwaPrefix + "setup-isolated-agent-git";
        public const string ActivitySetupIsolatedAgentTemp = AwaPrefix + "setup-isolated-agent-temp";
        public const string ActivitySetupWorktree = AwaPrefix + "setup-worktree";
        public const string ActivityCleanupIsolatedAgent = AwaPrefix + "cleanup-isolated-environment";
        public const string ActivityMergeWorktreeChanges = AwaPrefix + "merge-worktree-changes";
        public const string ActivityCopyAnalyzeOutputs = AwaPrefix + "copy-analyze-outputs";
        public const string ActivityGetParentWorkflowTaskQueue = AwaPrefix + "get-parent-workflow-task-queue";
        public const string ActivityReadJiraIssue = AwaPrefix + "read-jira-issue";
        public const string ActivityUpsertJiraIssue = AwaPrefix + "upsert-jira-issue";
        public const string ActivityAddJiraComment = AwaPrefix + "add-jira-comment";
        public const string ActivityGetTopLevelWorkflowInfo = AwaPrefix + "get-top-level-workflow-info";
        public const string ActivityChunkDocument = AwaPrefix + "chunk-document";
        public const string ActivityRunCommand = AwaPrefix + "run-command";
        public const string ActivityGenerateEmbeddings = AwaPrefix + "generate-embeddings";
        public const string ActivityWriteToVectorDb = AwaPrefix + "write-to-vector-db";
        public const string ActivityGenerateClarifyingQuestions = AwaPrefix + "generate-clarifying-questions";
        public const string ActivityGenerateContextualFollowUp = AwaPrefix + "generate-contextual-follow-up";
        public const string ActivityAnalyzeRequirements = AwaPrefix + "analyze-requirements";
        public const string ActivityWriteToS3VectorStore = AwaPrefix + "write-to-s3-vector-store";
        public const string ActivityGitClone = AwaPrefix + "git-clone";
        public const string ActivityResolveConfigVariables = AwaPrefix + "resolve-config-variables";

        // Workflow Names
        public const string WorkflowBuildPrompt = AwaPrefix + "build-prompt";
        public const string WorkflowHelloHuman = AwaPrefix + "hello-human";
        public const string WorkflowTransform = AwaPrefix + "transform";
        public const string WorkflowTransformBatch = AwaPrefix + "transform-batch";
        public const string WorkflowExecuteAgent = AwaPrefix + "execute-agent";
        public const string WorkflowApplySingleFileDiff = AwaPrefix + "apply-single-file-diff";
        public const string WorkflowResolveTemplate = AwaPrefix + "resolve-template";
        public const string WorkflowHelloWorld = AwaPrefix + "hello-world";
        public const string WorkflowHelloPoem = AwaPrefix + "hello-poem";
        public const string WorkflowHelloPoemAgent = AwaPrefix + "hello-poem-agent";
        public const string WorkflowTransformFile = AwaPrefix + "transform-file";
        public const string WorkflowCreatePrototypeFromFigma = AwaPrefix + "create-prototype-from-figma";
        public const string WorkflowParseSchema = AwaPrefix + "parse-schema";
        public const string WorkflowIsolatedAgent = AwaPrefix + "isolated-agent";
        public const string WorkflowChunkDocument = AwaPrefix + "chunk-document";
        public const string WorkflowReadFileAndParse = AwaPrefix + "read-file-and-parse";
        public const string WorkflowVectorDatabaseIngestion = AwaPrefix + "vector-database-ingestion";
        public const string WorkflowHitl = AwaPrefix + "hitl-child-workflow";
        public const string WorkflowIndexDocument = AwaPrefix + "index-document";
        public const string WorkflowGatherRequirements = AwaPrefix + "gather-requirements";
        public const string WorkflowAgentStreaming = AwaPrefix + "agent-streaming";
        public const string WorkflowOpenaiAgent = AwaPrefix + "openai-agent";
    }
}
