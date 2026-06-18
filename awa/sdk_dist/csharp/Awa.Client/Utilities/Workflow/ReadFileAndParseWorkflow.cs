using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Read and parse a file from a specified path, converting to markdown if supported.
        ///
        /// Uses MarkItDown to parse specific whitelisted document formats:
        /// - Documents: .pdf, .docx, .pptx, .xlsx, .xls
        /// - Web: .html, .htm
        /// - Data: .csv
        /// - E-books: .epub
        /// - Email: .msg (Outlook messages)
        ///
        /// All other file types (including .txt, .md, .py, etc.) are returned as-is without parsing
        /// when strict=False, or raise an exception when strict=True.
        /// </summary>
        /// <param name="filePath">The file path to read and parse</param>
        /// <param name="defaultValue">A string to return if the file does not exist</param>
        /// <param name="strict">If True, raise exception for unsupported file types; if False, return raw content</param>
        /// <returns>
        /// A string containing the parsed content (markdown) for supported formats,
        /// or raw content for unsupported formats when strict=False.
        /// </returns>
        /// <exception cref="Temporalio.Exceptions.ApplicationFailureException">When strict=True and file type is not supported</exception>
        public static async Task<string?> ReadFileAndParseWorkflow(
            string filePath,
            string? defaultValue = null,
            bool strict = false)
        {
            var input = new ReadFileAndParseInput
            {
                FilePath = filePath,
                DefaultContent = defaultValue,
                Strict = strict
            };

            var result = await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<string?>(
                AwaConstants.WorkflowReadFileAndParse,
                new object?[] { input },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue
                });

            return result;
        }
    }
}
