using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;
using Temporalio.Workflows;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Chunk a document into smaller pieces using various chunking strategies.
        ///
        /// This method executes the chunk document workflow which provides a consistent
        /// interface for document chunking across AWA. The workflow internally calls
        /// the chunk document activity and can be extended in the future to support
        /// additional features like caching or batch processing.
        /// </summary>
        /// <param name="content">The text content to be chunked</param>
        /// <param name="chunkerType">The type of chunker to use (TOKEN, SENTENCE, or RECURSIVE)</param>
        /// <param name="maxChunkSize">Maximum size of each chunk in tokens</param>
        /// <param name="chunkOverlap">Number of tokens to overlap between chunks</param>
        /// <returns>ChunkDocumentOutput containing the chunks and metadata</returns>
        public static async Task<ChunkDocumentOutput?> ChunkDocumentWorkflow(
            string content,
            ChunkerTypeEnum chunkerType = ChunkerTypeEnum.Recursive,
            int? maxChunkSize = null,
            int? chunkOverlap = null)
        {
            var inputData = new ChunkDocumentInput
            {
                Content = content,
                ChunkerType = chunkerType,
                MaxChunkSize = maxChunkSize,
                ChunkOverlap = chunkOverlap
            };

            return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<ChunkDocumentOutput?>(
                AwaConstants.WorkflowChunkDocument,
                new object?[] { inputData },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    Id = $"chunk-document-{Temporalio.Workflows.Workflow.Info.WorkflowId}"
                });
        }
    }
}
