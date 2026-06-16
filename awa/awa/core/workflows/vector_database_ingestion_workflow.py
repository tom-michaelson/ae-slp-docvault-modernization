"""Vector database ingestion workflow for preparing RAG corpora.

This workflow demonstrates an end-to-end process for ingesting documents into a vector
database for RAG applications. It reuses existing AWA building blocks for file parsing
and document chunking, then adds embedding generation and vector database storage.

The workflow follows AWA cookbook conventions and provides a simple, pluggable example
that can be extended for production use.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from temporalio import workflow
from temporalio.common import RetryPolicy

from awa.core.activities.generate_embeddings import generate_embeddings_activity
from awa.core.activities.write_to_s3_vector_store import write_to_s3_vector_store_activity
from awa.core.activities.write_to_vector_db import write_to_vector_db_activity
from awa.core.models.vector_ingestion_input import VectorIngestionInput
from awa.core.models.vector_ingestion_output import ChunkInfo, DocumentMetadata, EmbeddingResult, VectorIngestionOutput
from awa.core.workflows.chunk_document_workflow import ChunkDocumentWorkflow
from awa.core.workflows.read_file_and_parse_workflow import ReadFileAndParseWorkflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.chunking_models import ChunkDocumentInput
from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput

# Import activities with sandboxing for determinism
with workflow.unsafe.imports_passed_through():
    from awa.core.activities.file_io import list_directory_activity, write_file_activity
    from awa.core.logger.logger import LoggerComponent, get_logger


def _raise_no_chunks_error() -> None:
    """Raise error when no chunks were created from any files."""
    msg = "No chunks were created from any files"
    raise RuntimeError(msg)


def _generate_deterministic_id(prefix: str, file_path: str) -> str:
    """Generate a deterministic ID based only on file path."""
    # Use only the file path to ensure determinism across replays
    content = f"{prefix}-{file_path}"
    hash_obj = hashlib.md5(content.encode())  # noqa: S324
    hash_hex = hash_obj.hexdigest()[:8]
    return f"{prefix}-{Path(file_path).stem}-{hash_hex}"


@workflow.defn(name=sdk_constants.WORKFLOW_VECTOR_DATABASE_INGESTION)
class VectorDatabaseIngestionWorkflow:
    """Workflow for ingesting documents into a vector database.

    This workflow demonstrates a complete RAG corpus preparation pipeline:
    1. Read and parse documents using existing AWA workflows
    2. Chunk documents into smaller pieces
    3. Generate embeddings for each chunk
    4. Store embeddings in a vector database

    The workflow reuses existing AWA building blocks:
    - ReadFileAndParseWorkflow for document parsing
    - ChunkDocumentWorkflow for document chunking

    It provides a simple, end-to-end example that can be extended for production use.
    """

    @workflow.run
    async def run(self, workflow_input: VectorIngestionInput) -> VectorIngestionOutput:  # noqa: PLR0915
        """Execute the vector database ingestion workflow.

        Args:
            workflow_input: Configuration for the ingestion process

        Returns:
            VectorIngestionOutput with comprehensive information about the process

        """
        # The input is already validated as VectorIngestionInput by Temporal
        # No need for additional validation since the type system ensures it
        validated_input = workflow_input

        start_time = datetime.now(tz=UTC)
        logger = get_logger(LoggerComponent.WORKFLOW, workflow_id=workflow.info().workflow_id)

        logger.info("Starting vector database ingestion workflow")
        logger.info(f"Input directory: {validated_input.input_directory}")
        logger.info(f"Output directory: {validated_input.output_directory}")
        logger.info(f"Embedding model: {validated_input.embedding_model}")
        logger.info(f"Vector dimension: {validated_input.vector_dimension}")

        try:
            # Ensure output directory exists
            Path(validated_input.output_directory).mkdir(parents=True, exist_ok=True)

            # Step 1: List files in input directory
            files = await workflow.execute_activity(
                list_directory_activity,
                args=[validated_input.input_directory],
                start_to_close_timeout=timedelta(seconds=60),
            )

            # Filter for supported file types and limit if specified
            supported_extensions = {".pdf", ".docx", ".txt", ".md", ".html", ".csv"}
            filtered_files = [f for f in files if Path(f).suffix.lower() in supported_extensions]

            if validated_input.max_files:
                filtered_files = filtered_files[: validated_input.max_files]

            logger.info(f"Found {len(filtered_files)} files to process")

            # Step 2: Process each file
            all_chunks: list[ChunkInfo] = []
            documents_metadata: list[DocumentMetadata] = []

            for file_path in filtered_files:
                try:
                    logger.info(f"Processing file: {file_path}")

                    # Read and parse file
                    parse_input = ReadFileAndParseInput(
                        file_path=file_path,
                        default_content="",
                        strict=False,
                    )

                    parsed_content = await workflow.execute_child_workflow(
                        ReadFileAndParseWorkflow.run,
                        parse_input,
                        id=_generate_deterministic_id("parse", file_path),
                        task_queue=sdk_constants.AWA_DEFAULT_TASK_QUEUE,
                    )

                    # Chunk the parsed content
                    chunk_input = ChunkDocumentInput(
                        content=parsed_content,
                        chunker_type="recursive",
                        max_chunk_size=validated_input.chunk_size,
                        chunk_overlap=validated_input.chunk_overlap,
                    )

                    chunk_output = await workflow.execute_child_workflow(
                        ChunkDocumentWorkflow.run,
                        chunk_input,
                        id=_generate_deterministic_id("chunk", file_path),
                        task_queue=sdk_constants.AWA_DEFAULT_TASK_QUEUE,
                    )

                    # Convert chunks to our format
                    file_chunks = []
                    for i, chunk in enumerate(chunk_output.chunks):
                        # Create deterministic chunk ID
                        chunk_content = f"{file_path}-{i}"
                        chunk_hash = hashlib.md5(chunk_content.encode()).hexdigest()[:8]  # noqa: S324
                        chunk_info = ChunkInfo(
                            chunk_id=f"{Path(file_path).stem}_{i}_{chunk_hash}",
                            text=chunk.text,
                            token_count=chunk.token_count,
                            start_index=chunk.start_index,
                            end_index=chunk.end_index,
                        )
                        file_chunks.append(chunk_info)

                    # Create document metadata
                    file_stat = Path(file_path).stat()
                    doc_metadata = DocumentMetadata(
                        file_path=file_path,
                        file_size=file_stat.st_size,
                        file_type=Path(file_path).suffix.lower(),
                        processed_at=datetime.now(tz=UTC),
                        chunk_count=len(file_chunks),
                        embedding_count=0,  # Will be updated after embedding generation
                    )

                    all_chunks.extend(file_chunks)
                    documents_metadata.append(doc_metadata)

                    logger.info(f"Successfully processed {file_path}: {len(file_chunks)} chunks")

                except Exception:
                    logger.exception(f"Error processing file {file_path}")
                    continue

            if not all_chunks:
                _raise_no_chunks_error()

            logger.info(f"Total chunks created: {len(all_chunks)}")

            # Step 3: Generate embeddings
            logger.info("Generating embeddings for chunks")
            embedding_result: EmbeddingResult = await workflow.execute_activity(
                generate_embeddings_activity,
                args=[
                    all_chunks,
                    validated_input.embedding_model,  # Use embedding model from input
                    validated_input.vector_dimension,  # Use vector dimension from input
                ],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(maximum_attempts=1),  # No retries - fail immediately
            )

            # Extract chunks and embedding info
            chunks_with_embeddings = embedding_result.chunks
            actual_embedding_model = embedding_result.actual_model
            actual_provider = embedding_result.actual_provider

            # Update document metadata with embedding counts
            for doc_meta in documents_metadata:
                doc_meta.embedding_count = len(
                    [c for c in chunks_with_embeddings if c.chunk_id.startswith(Path(doc_meta.file_path).stem)],
                )

            logger.info(
                f"Generated embeddings for {len(chunks_with_embeddings)} chunks "
                f"using {actual_provider}:{actual_embedding_model}",
            )

            # Step 4: Write to vector database
            logger.info(
                f"Vector DB Type: '{validated_input.vector_db_type}' "
                f"(lower: '{validated_input.vector_db_type.lower()}')",
            )
            if validated_input.vector_db_type.lower() == "s3_vector":
                logger.info("✓ ROUTING TO S3 Vector Store")
                db_result = await workflow.execute_activity(
                    write_to_s3_vector_store_activity,
                    args=[
                        chunks_with_embeddings,
                        None,  # index_name - will use config default
                        True,  # create_index if it doesn't exist
                        100,  # batch_size
                    ],
                    start_to_close_timeout=timedelta(seconds=300),  # 5 minutes for S3 write
                )
                s3_result = db_result  # For consistency in output
            else:
                logger.info(f"✗ ROUTING TO traditional vector database: {validated_input.vector_db_type}")

                # Write to traditional vector database (ChromaDB, etc.)
                # Use output directory for vector database if no path specified
                vector_db_path = validated_input.vector_db_path
                if vector_db_path is None:
                    vector_db_path = str(
                        Path(validated_input.output_directory) / f"{validated_input.vector_db_type}_db",
                    )

                db_result = await workflow.execute_activity(
                    write_to_vector_db_activity,
                    args=[
                        chunks_with_embeddings,
                        validated_input.vector_db_type,
                        vector_db_path,
                        None,  # collection_name - will use default
                        {
                            "workflow_id": workflow.info().workflow_id,
                            "embedding_model": actual_embedding_model,
                            "embedding_provider": actual_provider,
                        },
                    ],
                    start_to_close_timeout=timedelta(seconds=300),  # 5 minutes for DB write
                )

                # Don't write to S3 Vector Store when using traditional databases
                # Only write to S3 when explicitly requested via vector_db_type="s3_vector"
                logger.info("Skipping S3 Vector Store - only used when vector_db_type='s3_vector'")
                s3_result = {"status": "skipped", "reason": "S3 Vector Store only used when vector_db_type='s3_vector'"}

            # Step 5: Create output files
            end_time = datetime.now(tz=UTC)
            processing_time = (end_time - start_time).total_seconds()

            # Create metadata file
            metadata_file = Path(validated_input.output_directory) / "ingestion_metadata.json"

            # Prepare configuration with actual model used
            config_dict = validated_input.model_dump()
            config_dict["actual_embedding_model"] = actual_embedding_model
            config_dict["actual_embedding_provider"] = actual_provider

            metadata_content = {
                "workflow_id": workflow.info().workflow_id,
                "processing_start": start_time.isoformat(),
                "processing_end": end_time.isoformat(),
                "total_processing_time_seconds": processing_time,
                "configuration": config_dict,
                "database_result": db_result,
                "s3_vector_result": s3_result,
                "documents_processed": len(documents_metadata),
                "total_chunks": len(all_chunks),
                "total_embeddings": len(chunks_with_embeddings),
            }

            await workflow.execute_activity(
                write_file_activity,
                args=[str(metadata_file), json.dumps(metadata_content, indent=2)],
                start_to_close_timeout=timedelta(seconds=60),
            )

            # Create summary file
            summary_file = Path(validated_input.output_directory) / "ingestion_summary.txt"
            summary_content = f"""Vector Database Ingestion Summary
=====================================

Workflow ID: {workflow.info().workflow_id}
Processing Time: {processing_time:.2f} seconds

Configuration:
- Input Directory: {validated_input.input_directory}
- Output Directory: {validated_input.output_directory}
- Chunk Size: {validated_input.chunk_size}
- Chunk Overlap: {validated_input.chunk_overlap}
- Embedding Model: {actual_embedding_model} ({actual_provider})
- Vector Dimension: {validated_input.vector_dimension}
- Vector DB Type: {validated_input.vector_db_type}

Results:
- Documents Processed: {len(documents_metadata)}
- Total Chunks Created: {len(all_chunks)}
- Total Embeddings Generated: {len(chunks_with_embeddings)}
- Vector Database: {validated_input.vector_db_type}
- Index/Collection: {db_result.get("index_name") or db_result.get("collection_name", "N/A")}

Files Processed:
"""
            for doc_meta in documents_metadata:
                summary_content += (
                    f"- {doc_meta.file_path}: {doc_meta.chunk_count} chunks, {doc_meta.embedding_count} embeddings\n"
                )

            await workflow.execute_activity(
                write_file_activity,
                args=[str(summary_file), summary_content],
                start_to_close_timeout=timedelta(seconds=60),
            )

            # Create output object
            output = VectorIngestionOutput(
                total_documents_processed=len(documents_metadata),
                total_chunks_created=len(all_chunks),
                total_embeddings_generated=len(chunks_with_embeddings),
                documents_metadata=documents_metadata,
                chunks_info=chunks_with_embeddings,
                vector_db_type=validated_input.vector_db_type,
                vector_db_path=db_result.get("vector_db_path", "N/A"),
                collection_name=db_result.get("collection_name", db_result.get("index_name", "N/A")),
                output_directory=validated_input.output_directory,
                metadata_file=str(metadata_file),
                summary_file=str(summary_file),
                processing_start_time=start_time,
                processing_end_time=end_time,
                total_processing_time_seconds=processing_time,
                chunk_size=validated_input.chunk_size,
                chunk_overlap=validated_input.chunk_overlap,
                embedding_model=validated_input.embedding_model,
                success=True,
                errors=[],
            )

            logger.info("Vector database ingestion completed successfully")
            logger.info(f"Processed {len(documents_metadata)} documents")
            logger.info(f"Created {len(all_chunks)} chunks")
            logger.info(f"Generated {len(chunks_with_embeddings)} embeddings")
            logger.info(f"Stored in {validated_input.vector_db_type} database")

            return output

        except Exception:
            logger.exception("Vector database ingestion workflow failed")
            # Let all exceptions (including embedding failures) fail the workflow
            raise
