"""Generic workflow for chunking and summarizing content that may exceed context limits."""

import os
from pathlib import Path

from temporalio import workflow

from cookbook.recipes import constants
from cookbook.recipes.models.chunking import ChunkAndSummarizeInput, ChunkAndSummarizeResult
from cookbook.recipes.utilities.chunking_utils import calculate_total_length, create_chunks, needs_chunking

with workflow.unsafe.imports_passed_through():
    from cookbook.recipes.utilities.chunking_utils import ContentChunk

from sdk_dist.python.awa.client import awa_workflow
from sdk_dist.python.awa.client.models import TransformParams

MAX_CONCURRENT_TRANSFORMS = os.environ.get("MAX_CONCURRENT_TRANSFORMS", constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS)


@workflow.defn(name="chunk-and-summarize-workflow")
class ChunkAndSummarizeWorkflow:
    """A reusable workflow for chunking and summarizing content that may exceed context limits.

    This workflow can be used by any parent workflow that needs to handle potentially
    large content by:
    1. Checking if content exceeds limits
    2. Chunking the content intelligently
    3. Summarizing each chunk
    4. Combining summaries into a final result
    5. Iteratively summarizing if needed
    """

    @workflow.run
    async def run(self, workflow_input: ChunkAndSummarizeInput) -> ChunkAndSummarizeResult:
        """Execute the chunk and summarize workflow.

        Args:
            workflow_input: Configuration for chunking and summarization

        Returns:
            ChunkAndSummarizeResult with final summary and metadata

        """
        # Calculate total content length
        total_length = calculate_total_length(workflow_input.content_items)

        # If content is within limits, return it as-is or create a simple summary
        if not needs_chunking(workflow_input.content_items, workflow_input.max_content_length):
            workflow.logger.info(
                f"Content within limits ({total_length} chars), no chunking needed",
            )

            # If we have BAML configuration, create a single summary
            if workflow_input.baml_path:
                final_summary = await self._create_single_summary(workflow_input)
            else:
                # Just join the content items
                final_summary = "\n".join(workflow_input.content_items)

            return ChunkAndSummarizeResult(
                final_summary=final_summary,
                chunk_summaries=[],
                was_chunked=False,
                num_chunks=1,
                total_original_length=total_length,
                iterations_performed=0,
            )

        # Content exceeds limits, need to chunk and summarize
        workflow.logger.info(
            f"Content exceeds limits ({total_length} > {workflow_input.max_content_length}), "
            f"chunking with strategy: {workflow_input.chunking_strategy}",
        )

        # Perform iterative chunking and summarization
        final_summary, chunk_summaries, iterations = await self._iterative_chunk_and_summarize(
            workflow_input,
        )

        return ChunkAndSummarizeResult(
            final_summary=final_summary,
            chunk_summaries=chunk_summaries,
            was_chunked=True,
            num_chunks=len(chunk_summaries),
            total_original_length=total_length,
            iterations_performed=iterations,
        )

    async def _create_single_summary(self, workflow_input: ChunkAndSummarizeInput) -> str:
        """Create a summary when no chunking is needed."""
        # Use the final summary function with all content
        transform_params = TransformParams(
            baml_function_name=workflow_input.final_summary_function,
            request={
                "chunk_summaries": workflow_input.content_items,
                "context_data": workflow_input.context_data,
            },
        )
        return await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(workflow_input.baml_path)) if workflow_input.baml_path else None,
        )

    async def _iterative_chunk_and_summarize(
        self,
        workflow_input: ChunkAndSummarizeInput,
    ) -> tuple[str, list[str], int]:
        """Chunk and summarize content iteratively until it fits within limits.

        Returns:
            Tuple of (final_summary, chunk_summaries, iterations_performed)

        """
        iterations = 0
        current_items = workflow_input.content_items
        all_summaries = []

        while True:
            iterations += 1
            workflow.logger.info(f"Starting iteration {iterations} of chunking")

            # Create chunks
            chunks = create_chunks(
                current_items,
                workflow_input.max_chunk_length,
                workflow_input.chunking_strategy,
            )

            workflow.logger.info(f"Created {len(chunks)} chunks in iteration {iterations}")

            # Summarize each chunk in parallel
            chunk_summaries = await self._summarize_chunks_parallel(
                chunks,
                workflow_input,
                iteration=iterations,
            )

            # Store these summaries
            if iterations == 1:
                all_summaries = chunk_summaries

            # Check if the summaries themselves need chunking
            summary_length = calculate_total_length(chunk_summaries)

            if not workflow_input.iterative_summarization:
                # No iterative summarization, create final summary regardless of size
                workflow.logger.info("Iterative summarization disabled, creating final summary")
                break

            if summary_length <= workflow_input.max_content_length:
                # Summaries fit within limits, create final summary
                workflow.logger.info(
                    f"Summaries within limits ({summary_length} chars), creating final summary",
                )
                break

            # Summaries still too large, need another iteration
            workflow.logger.info(
                f"Summaries exceed limits ({summary_length} > {workflow_input.max_content_length}), "
                "continuing iteration",
            )

            current_items = chunk_summaries

            # Safety check to prevent infinite loops
            max_iterations = 10
            if iterations >= max_iterations:
                workflow.logger.warning("Maximum iterations reached, creating final summary anyway")
                break

        # Create final summary from chunk summaries
        if workflow_input.baml_path:
            final_summary = await self._create_final_summary(chunk_summaries, workflow_input)
        else:
            final_summary = "\n\n".join(chunk_summaries)

        return final_summary, all_summaries, iterations

    async def _summarize_chunks_parallel(
        self,
        chunks: list[ContentChunk],
        workflow_input: ChunkAndSummarizeInput,
        iteration: int,
    ) -> list[str]:
        """Summarize multiple chunks in parallel with controlled concurrency."""
        # Create coroutine functions for all chunks
        coroutine_funcs = [
            lambda chunk=chunk: self._summarize_single_chunk(chunk, workflow_input, iteration) for chunk in chunks
        ]

        # Run with controlled concurrency
        results = await awa_workflow.run_with_controlled_concurrency(
            coroutine_funcs=coroutine_funcs,
            max_concurrency=MAX_CONCURRENT_TRANSFORMS,
        )

        return results

    async def _summarize_single_chunk(
        self,
        chunk: ContentChunk,
        workflow_input: ChunkAndSummarizeInput,
        iteration: int,
    ) -> str:
        """Summarize a single chunk using BAML transform."""
        if not workflow_input.baml_path:
            # No BAML configuration, just join the items
            return "\n".join(chunk.items)

        # Add chunk metadata to context
        context_with_chunk = dict(workflow_input.context_data)
        context_with_chunk["iteration"] = str(iteration)

        transform_params = TransformParams(
            baml_function_name=workflow_input.chunk_summary_function,
            request={
                "content_items": chunk.items,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "context_data": context_with_chunk,
            },
        )
        return await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(workflow_input.baml_path)),
        )

    async def _create_final_summary(
        self,
        chunk_summaries: list[str],
        workflow_input: ChunkAndSummarizeInput,
    ) -> str:
        """Create the final summary from chunk summaries."""
        transform_params = TransformParams(
            baml_function_name=workflow_input.final_summary_function,
            request={
                "chunk_summaries": chunk_summaries,
                "context_data": workflow_input.context_data,
            },
        )
        return await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(workflow_input.baml_path)) if workflow_input.baml_path else None,
        )
