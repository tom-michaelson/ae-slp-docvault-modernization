"""Integration test script for vector database ingestion workflow.

This script provides a simple way to test the workflow with sample data.
It can be run independently to verify the workflow functions correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path

from awa.core.models.vector_ingestion_input import VectorIngestionInput
from awa.core.workflows.vector_database_ingestion_workflow import (
    VectorDatabaseIngestionWorkflow,
)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging for the test
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def test_workflow_models() -> bool:
    """Test that the workflow models can be created and validated."""
    logger.info("Testing workflow models...")

    try:
        # Test input model creation
        input_config = VectorIngestionInput(
            input_directory="test-data/input/",
            output_directory="test-data/output/",
            embedding_model="tfidf-svd",  # Now required
            chunk_size=256,  # Smaller chunks for testing
            chunk_overlap=25,
            max_files=2,  # Limit to test files
        )

        logger.info("✅ Input model created successfully")
        logger.info(f"   - Input directory: {input_config.input_directory}")
        logger.info(f"   - Output directory: {input_config.output_directory}")
        logger.info(f"   - Chunk size: {input_config.chunk_size}")
        logger.info(f"   - Max files: {input_config.max_files}")

        # Test output model creation (mock data)
        from datetime import datetime

        from awa.core.models.vector_ingestion_output import (
            ChunkInfo,
            DocumentMetadata,
            VectorIngestionOutput,
        )

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        doc_meta = DocumentMetadata(
            file_path="test.txt",
            file_size=100,
            file_type=".txt",
            processed_at=now,
            chunk_count=1,
            embedding_count=1,
        )

        chunk_info = ChunkInfo(
            chunk_id="test_chunk",
            text="Test content",
            token_count=3,
            start_index=0,
            end_index=12,
        )

        output = VectorIngestionOutput(
            total_documents_processed=1,
            total_chunks_created=1,
            total_embeddings_generated=1,
            documents_metadata=[doc_meta],
            chunks_info=[chunk_info],
            vector_db_type="chroma",
            vector_db_path="./test_chroma_db",
            collection_name="test_collection",
            output_directory="test-data/output/",
            metadata_file="test-data/output/metadata.json",
            summary_file="test-data/output/summary.txt",
            processing_start_time=now,
            processing_end_time=now,
            total_processing_time_seconds=1.0,
            chunk_size=256,
            chunk_overlap=25,
            embedding_model="text-embedding-ada-002",
            success=True,
            errors=[],
        )

        logger.info("✅ Output model created successfully")
        logger.info(f"   - Total documents: {output.total_documents_processed}")
        logger.info(f"   - Total chunks: {output.total_chunks_created}")
        logger.info(f"   - Success: {output.success}")

        return True

    except Exception:
        logger.exception("❌ Model test failed")
        return False


async def test_workflow_creation() -> bool:
    """Test that the workflow class can be created."""
    logger.info("Testing workflow creation...")

    try:
        # Test that we can create the workflow class
        VectorDatabaseIngestionWorkflow()
        logger.info("✅ Workflow class created successfully")
        return True

    except Exception:
        logger.exception("❌ Workflow creation failed")
        return False


async def test_dependency_checking() -> bool:
    """Test that missing dependencies are properly detected."""
    logger.info("Testing dependency checking...")

    try:
        # Test scikit-learn dependency (for TF-IDF embeddings)
        try:
            import sklearn  # noqa: F401

            logger.info("✅ scikit-learn package is available")
        except ImportError:
            logger.warning("❌ scikit-learn package is missing")
            return False

        # Test ChromaDB dependency
        try:
            import chromadb  # noqa: F401

            logger.info("✅ ChromaDB package is available")
        except ImportError:
            logger.warning("❌ ChromaDB package is missing")
            return False

        # Test that activities work with the new TF-IDF approach
        from awa.core.activities.generate_embeddings import generate_embeddings_activity
        from awa.core.models.vector_ingestion_output import ChunkInfo

        # Create test chunks
        chunks = [
            ChunkInfo(
                chunk_id="test_chunk",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
            ),
        ]

        # Test that the activity works with TF-IDF
        try:
            result = await generate_embeddings_activity(chunks, "tfidf-svd", 128)
            logger.info("✅ Activity successfully generates embeddings with TF-IDF")
            assert len(result) == 1
            assert result[0].embedding_vector is not None
        except Exception:
            logger.exception("❌ Activity failed unexpectedly")
            return False

        return True

    except Exception:
        logger.exception("❌ Dependency checking failed")
        return False


async def test_file_structure() -> bool:
    """Test that the required files and directories exist."""
    logger.info("Testing file structure...")

    # The test file is in tests/workflow/tests/, so we need to go up one level to find test-data
    test_file_dir = Path(__file__).parent
    workflow_dir = test_file_dir.parent  # This is tests/workflow/

    # Check for core workflow files - they should be in the main project directories
    project_root = test_file_dir.parent.parent.parent
    core_workflow_dir = project_root / "awa" / "core" / "workflows"
    core_activities_dir = project_root / "awa" / "core" / "activities"
    core_models_dir = project_root / "awa" / "core" / "models"

    required_core_files = [
        (core_workflow_dir, "vector_database_ingestion_workflow.py"),
        (core_activities_dir, "generate_embeddings.py"),
        (core_activities_dir, "write_to_vector_db.py"),
        (core_models_dir, "vector_ingestion_input.py"),
        (core_models_dir, "vector_ingestion_output.py"),
    ]

    required_test_files = [
        "test_vector_ingestion_models.py",
        "test_integration.py",
    ]

    required_dirs = [
        "test-data/input",
        "test-data/output",
    ]

    all_good = True

    # Check core files
    for core_dir, file_name in required_core_files:
        full_path = core_dir / file_name
        if full_path.exists():
            logger.info(f"✅ Core file exists: {file_name}")
        else:
            logger.warning(f"❌ Core file missing: {file_name}")
            all_good = False

    # Check test files
    for file_name in required_test_files:
        full_path = test_file_dir / file_name
        if full_path.exists():
            logger.info(f"✅ Test file exists: {file_name}")
        else:
            logger.warning(f"❌ Test file missing: {file_name}")
            all_good = False

    # Check required directories
    for dir_path in required_dirs:
        full_path = workflow_dir / dir_path
        logger.info(f"Checking directory: {full_path} (exists: {full_path.exists()})")
        if full_path.exists():
            logger.info(f"✅ Directory exists: {dir_path}")
        else:
            logger.warning(f"❌ Directory missing: {dir_path}")
            all_good = False

    # Check test data files
    test_data_dir = workflow_dir / "test-data" / "input"
    if test_data_dir.exists():
        test_files = list(test_data_dir.glob("*"))
        if test_files:
            logger.info(f"✅ Test data files found: {len(test_files)} files")
            for test_file in test_files:
                logger.info(f"   - {test_file.name}")
        else:
            logger.warning(f"❌ No test data files found in {test_data_dir}")
            all_good = False
    else:
        logger.warning("❌ Test data directory missing: test-data/input/")
        all_good = False

    return all_good


async def main() -> int:
    """Run the main test function."""
    logger.info("🧪 Vector Database Ingestion Workflow Integration Test")
    logger.info("=" * 60)

    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent / "test-data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run tests
    tests = [
        test_workflow_models(),
        test_workflow_creation(),
        test_dependency_checking(),
        test_file_structure(),
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    # Summarize results
    logger.info("\n%s", "=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Test {i + 1} failed with exception: {result}")
        elif result:
            logger.info(f"✅ Test {i + 1} passed")
            passed += 1
        else:
            logger.error(f"❌ Test {i + 1} failed")

    logger.info(f"\nOverall Result: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! The workflow is ready for use.")
        return 0
    logger.warning("⚠️  Some tests failed. Please review the issues above.")
    return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception:
        logger.exception("\n\n💥 Unexpected error")
        sys.exit(1)
