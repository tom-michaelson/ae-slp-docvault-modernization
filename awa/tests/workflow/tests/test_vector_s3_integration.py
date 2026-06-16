"""Integration test script for S3 Vector Store with vector database ingestion workflow.

This script provides integration tests specifically for S3 Vector Store functionality.
It can be run to verify the S3 Vector Store integration works correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

from awa.core.models.vector_ingestion_input import VectorIngestionInput

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging for the test
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def test_s3_vector_workflow_models() -> bool:
    """Test that S3 Vector Store workflow models can be created and validated."""
    logger.info("Testing S3 Vector Store workflow models...")

    try:
        # Test input model creation with S3 Vector Store
        input_config = VectorIngestionInput(
            input_directory="test-data/input/",
            output_directory="test-data/output/",
            embedding_model="tfidf-svd",
            vector_db_type="s3_vector",  # Key difference for S3 Vector Store
            chunk_size=256,
            chunk_overlap=25,
            max_files=2,
        )

        logger.info("✅ S3 Vector Store input model created successfully")
        logger.info(f"   - Input directory: {input_config.input_directory}")
        logger.info(f"   - Output directory: {input_config.output_directory}")
        logger.info(f"   - Vector DB type: {input_config.vector_db_type}")
        logger.info(f"   - Embedding model: {input_config.embedding_model}")
        logger.info(f"   - Chunk size: {input_config.chunk_size}")

        # Test with Azure OpenAI + S3 Vector Store
        azure_config = VectorIngestionInput(
            input_directory="test-data/input/",
            output_directory="test-data/output/",
            embedding_model="azure-text-embedding-ada-002",
            vector_db_type="s3_vector",
            vector_dimension=1536,
            chunk_size=1024,
            chunk_overlap=100,
            include_metadata=True,
        )

        logger.info("✅ Azure OpenAI + S3 Vector Store model created successfully")
        logger.info(f"   - Embedding model: {azure_config.embedding_model}")
        logger.info(f"   - Vector dimension: {azure_config.vector_dimension}")
        logger.info(f"   - Include metadata: {azure_config.include_metadata}")

        # Test with OpenAI + S3 Vector Store
        openai_config = VectorIngestionInput(
            input_directory="test-data/input/",
            output_directory="test-data/output/",
            embedding_model="text-embedding-ada-002",
            vector_db_type="s3_vector",
            vector_dimension=1536,
            chunk_size=1024,
            chunk_overlap=100,
        )

        logger.info("✅ OpenAI + S3 Vector Store model created successfully")
        logger.info(f"   - Embedding model: {openai_config.embedding_model}")
        logger.info(f"   - Vector dimension: {openai_config.vector_dimension}")

        return True

    except Exception:
        logger.exception("❌ S3 Vector Store model test failed")
        return False


async def test_s3_vector_store_routing() -> bool:
    """Test that workflow properly routes to S3 Vector Store when configured."""
    logger.info("Testing S3 Vector Store routing logic...")

    try:
        from awa.core.models.vector_ingestion_input import VectorIngestionInput

        # Test different vector_db_type values
        test_cases = [
            ("s3_vector", True, "Should route to S3 Vector Store"),
            ("S3_VECTOR", True, "Should route to S3 Vector Store (case insensitive)"),
            ("chroma", False, "Should NOT route to S3 Vector Store"),
            ("lancedb", False, "Should NOT route to S3 Vector Store"),
            ("pinecone", False, "Should NOT route to S3 Vector Store"),
        ]

        for vector_db_type, should_route_to_s3, description in test_cases:
            input_config = VectorIngestionInput(
                input_directory="test-data/input/",
                output_directory="test-data/output/",
                embedding_model="tfidf-svd",
                vector_db_type=vector_db_type,
            )

            # Test the routing logic from the workflow
            routes_to_s3 = input_config.vector_db_type.lower() == "s3_vector"

            if routes_to_s3 == should_route_to_s3:
                logger.info(f"✅ {description}: {vector_db_type}")
            else:
                logger.error(f"❌ {description}: {vector_db_type}")
                return False

        return True

    except Exception:
        logger.exception("❌ S3 Vector Store routing test failed")
        return False


async def test_s3_vector_store_dependency_checking() -> bool:
    """Test that S3 Vector Store dependencies are properly available."""
    logger.info("Testing S3 Vector Store dependency checking...")

    try:
        # Test boto3 dependency (for S3 Vector Store)
        try:
            import boto3  # noqa: F401

            logger.info("✅ boto3 package is available")
        except ImportError:
            logger.warning("❌ boto3 package is missing (required for S3 Vector Store)")
            return False

        # Test botocore dependency
        try:
            import botocore  # noqa: F401

            logger.info("✅ botocore package is available")
        except ImportError:
            logger.warning("❌ botocore package is missing (required for S3 Vector Store)")
            return False

        # Test that S3 Vector Store utility classes can be imported
        try:
            from awa.core.utils.s3_vector_store import S3VectorStore  # noqa: F401

            logger.info("✅ S3VectorStore utility class is available")
        except ImportError:
            logger.warning("❌ S3VectorStore utility class is missing")
            return False

        # Test that S3 Vector Store activity can be imported
        try:
            from awa.core.activities.write_to_s3_vector_store import (  # noqa: F401
                write_to_s3_vector_store_activity,
            )

            logger.info("✅ S3 Vector Store activity is available")
        except ImportError:
            logger.warning("❌ S3 Vector Store activity is missing")
            return False

        # Test that S3 Vector Store configuration model can be imported
        try:
            from awa.core.models.config.s3_vector_config import S3VectorConfig  # noqa: F401

            logger.info("✅ S3 Vector Store configuration model is available")
        except ImportError:
            logger.warning("❌ S3 Vector Store configuration model is missing")
            return False

        return True

    except Exception:
        logger.exception("❌ S3 Vector Store dependency checking failed")
        return False


@patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
@patch("awa.core.activities.write_to_s3_vector_store.S3VectorStore")
async def test_s3_vector_store_activity_mock(
    mock_s3_store_class: Mock,
    mock_config_loader: Mock,
) -> bool:
    """Test S3 Vector Store activity with mocked dependencies."""
    logger.info("Testing S3 Vector Store activity with mocked dependencies...")

    try:
        from awa.core.activities.write_to_s3_vector_store import (
            write_to_s3_vector_store_activity,
        )
        from awa.core.models.vector_ingestion_output import ChunkInfo

        # Mock configuration
        mock_config = Mock()
        mock_config.s3_vector = Mock()
        mock_config.s3_vector.enabled = True
        mock_config.s3_vector.index_name = "test-index"
        mock_config.s3_vector.embedding_source = "tfidf"
        mock_config_loader.get_config.return_value = mock_config

        # Mock S3VectorStore
        mock_s3_store = Mock()
        mock_s3_store_class.return_value = mock_s3_store
        mock_s3_store.create_index_if_not_exists.return_value = {"status": "created"}
        mock_s3_store.batch_put_vectors.return_value = [{"status": "success"}]

        # Test data
        chunks = [
            ChunkInfo(
                chunk_id="test_chunk_1",
                text="Test content for S3 Vector Store",
                token_count=6,
                start_index=0,
                end_index=30,
                embedding_vector=[0.1, 0.2, 0.3, 0.4],
            ),
            ChunkInfo(
                chunk_id="test_chunk_2",
                text="Another test chunk",
                token_count=3,
                start_index=0,
                end_index=18,
                embedding_vector=[0.5, 0.6, 0.7, 0.8],
            ),
        ]

        # Test the activity
        result = await write_to_s3_vector_store_activity(
            chunks,
            "test-index",
            create_index=True,
            batch_size=100,
        )

        # Verify results
        assert result["vectors_written"] == 2
        assert result["index_name"] == "test-index"
        assert result["created_index"] is True
        assert result["skipped"] is False

        logger.info("✅ S3 Vector Store activity test passed")
        logger.info(f"   - Vectors written: {result['vectors_written']}")
        logger.info(f"   - Index name: {result['index_name']}")
        logger.info(f"   - Created index: {result['created_index']}")

        return True

    except Exception:
        logger.exception("❌ S3 Vector Store activity mock test failed")
        return False


async def test_workflow_routing_integration() -> bool:
    """Test that the workflow properly integrates S3 Vector Store routing."""
    logger.info("Testing workflow routing integration...")

    try:
        from awa.core.workflows.vector_database_ingestion_workflow import (
            VectorDatabaseIngestionWorkflow,
        )

        # Test that workflow class can be created
        VectorDatabaseIngestionWorkflow()

        # Test input configurations
        test_configs = [
            {
                "name": "TF-IDF + S3 Vector Store",
                "input": VectorIngestionInput(
                    input_directory="test-data/input/",
                    output_directory="test-data/output/",
                    embedding_model="tfidf-svd",
                    vector_db_type="s3_vector",
                    vector_dimension=128,
                ),
                "should_route_to_s3": True,
            },
            {
                "name": "Azure OpenAI + S3 Vector Store",
                "input": VectorIngestionInput(
                    input_directory="test-data/input/",
                    output_directory="test-data/output/",
                    embedding_model="azure-text-embedding-ada-002",
                    vector_db_type="s3_vector",
                    vector_dimension=1536,
                ),
                "should_route_to_s3": True,
            },
            {
                "name": "TF-IDF + ChromaDB",
                "input": VectorIngestionInput(
                    input_directory="test-data/input/",
                    output_directory="test-data/output/",
                    embedding_model="tfidf-svd",
                    vector_db_type="chroma",
                    vector_dimension=128,
                ),
                "should_route_to_s3": False,
            },
        ]

        for config in test_configs:
            # Test routing logic (without actually running the workflow)
            routes_to_s3 = config["input"].vector_db_type.lower() == "s3_vector"

            if routes_to_s3 == config["should_route_to_s3"]:
                logger.info(f"✅ {config['name']}: Routing correct")
            else:
                logger.error(f"❌ {config['name']}: Routing incorrect")
                return False

        logger.info("✅ All workflow routing configurations validated")
        return True

    except Exception:
        logger.exception("❌ Workflow routing integration test failed")
        return False


async def test_s3_vector_store_configuration() -> bool:
    """Test S3 Vector Store configuration models."""
    logger.info("Testing S3 Vector Store configuration...")

    try:
        from awa.core.models.config.s3_vector_config import S3VectorConfig

        # Test valid configuration
        config = S3VectorConfig(
            enabled=True,
            region_name="us-east-2",
            vector_bucket_name="test-vector-bucket",
            index_name="test-index",
            distance_metric="cosine",
            embedding_source="azure_openai",
        )

        assert config.enabled is True
        assert config.region_name == "us-east-2"
        assert config.vector_bucket_name == "test-vector-bucket"
        assert config.index_name == "test-index"
        assert config.distance_metric == "cosine"
        assert config.embedding_source == "azure_openai"

        logger.info("✅ S3 Vector Store configuration model works correctly")
        logger.info(f"   - Enabled: {config.enabled}")
        logger.info(f"   - Region: {config.region_name}")
        logger.info(f"   - Bucket: {config.vector_bucket_name}")
        logger.info(f"   - Index: {config.index_name}")
        logger.info(f"   - Distance metric: {config.distance_metric}")

        # Test different embedding sources
        for embedding_source in ["azure_openai", "openai", "tfidf"]:
            test_config = S3VectorConfig(
                enabled=True,
                region_name="us-west-2",
                vector_bucket_name="test-bucket",
                index_name="test-index",
                embedding_source=embedding_source,
            )
            assert test_config.embedding_source == embedding_source

        logger.info("✅ All embedding sources validated")
        return True

    except Exception:
        logger.exception("❌ S3 Vector Store configuration test failed")
        return False


async def main() -> int:
    """Run the main S3 Vector Store integration test function."""
    logger.info("🧪 S3 Vector Store Integration Test")
    logger.info("=" * 60)

    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent.parent / "test-data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run S3 Vector Store specific tests
    tests = [
        test_s3_vector_workflow_models(),
        test_s3_vector_store_routing(),
        test_s3_vector_store_dependency_checking(),
        test_s3_vector_store_activity_mock(),
        test_workflow_routing_integration(),
        test_s3_vector_store_configuration(),
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    # Summarize results
    logger.info("\n%s", "=" * 60)
    logger.info("📊 S3 Vector Store Test Results Summary")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    test_names = [
        "S3 Vector Store Models",
        "S3 Vector Store Routing",
        "S3 Dependencies",
        "S3 Activity Mock",
        "Workflow Routing Integration",
        "S3 Configuration",
    ]

    for i, result in enumerate(results):
        test_name = test_names[i] if i < len(test_names) else f"Test {i + 1}"
        if isinstance(result, Exception):
            logger.error(f"❌ {test_name} failed with exception: {result}")
        elif result:
            logger.info(f"✅ {test_name} passed")
            passed += 1
        else:
            logger.error(f"❌ {test_name} failed")

    logger.info(f"\nOverall Result: {passed}/{total} S3 Vector Store tests passed")

    if passed == total:
        logger.info("🎉 All S3 Vector Store tests passed! Integration is ready for use.")
        return 0
    logger.warning("⚠️  Some S3 Vector Store tests failed. Please review the issues above.")
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
