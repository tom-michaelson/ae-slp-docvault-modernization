# tests/workflow/test_cases/chromadb_query_utils.py
# Utility functions for querying and exploring ChromaDB embeddings
# This file provides tools to search, explore, and analyze stored embeddings

import json
import logging
import sys
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class ChromaDBQueryUtils:
    """Utility class for querying and exploring ChromaDB embeddings."""

    def __init__(self, db_path: str = "./chroma_db") -> None:
        """Initialize the ChromaDB query utilities.

        Args:
            db_path: Path to the ChromaDB database

        """
        self.db_path = Path(db_path)
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False),
        )

    def list_collections(self) -> list[str]:
        """List all available collections in the database.

        Returns:
            List of collection names

        """
        try:
            logger.info(f"🔍 Connecting to ChromaDB at: {self.db_path}")
            logger.info(f"🔍 Database exists: {self.db_path.exists()}")

            collections = self.client.list_collections()
            logger.info(f"🔍 Raw collections response: {collections}")

            if collections:
                collection_names = [col.name for col in collections]
                logger.info(f"🔍 Found collection names: {collection_names}")
                return collection_names
            logger.info("🔍 No collections returned from ChromaDB")
            return []

        except Exception:
            logger.exception("❌ Error listing collections")
            import traceback

            traceback.print_exc()
            return []

    def get_collection_info(self, collection_name: str) -> dict[str, Any] | None:
        """Get detailed information about a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection information or None if not found

        """
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()

            # Get a sample of documents to understand structure
            sample = collection.get(limit=1)

            return {
                "name": collection_name,
                "document_count": count,
                "sample_document": sample.get("documents", [None])[0] if sample.get("documents") else None,
                "sample_metadata": sample.get("metadatas", [None])[0] if sample.get("metadatas") else None,
                "embedding_dimension": len(sample.get("embeddings", [[]])[0]) if sample.get("embeddings") else 0,
            }
        except Exception:
            logger.exception(f"Error getting collection info for '{collection_name}'")
            return None

    def search_similar_texts(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        include_metadata: bool = True,  # noqa: ARG002
    ) -> dict[str, Any] | None:
        """Search for similar texts using semantic similarity.

        Args:
            collection_name: Name of the collection to search
            query_text: Text to search for
            n_results: Number of results to return
            include_metadata: Whether to include metadata in results

        Returns:
            Search results or None if error occurs

        """
        try:
            collection = self.client.get_collection(name=collection_name)

            # Perform the search
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            return {
                "query": query_text,
                "results": [
                    {
                        "document": doc,
                        "metadata": meta,
                        "distance": dist,
                        "rank": i + 1,
                    }
                    for i, (doc, meta, dist) in enumerate(
                        zip(
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0],
                            strict=False,
                        ),
                    )
                ],
            }
        except Exception:
            logger.exception(f"Error searching collection '{collection_name}'")
            return None

    def get_documents_by_metadata(
        self,
        collection_name: str,
        metadata_filter: dict[str, Any],
        limit: int = 10,
    ) -> dict[str, Any] | None:
        """Get documents filtered by metadata.

        Args:
            collection_name: Name of the collection
            metadata_filter: Dictionary of metadata key-value pairs to filter by
            limit: Maximum number of documents to return

        Returns:
            Filtered documents or None if error occurs

        """
        try:
            collection = self.client.get_collection(name=collection_name)

            # Build the where clause for metadata filtering
            where_clause = {}
            for key, value in metadata_filter.items():
                where_clause[key] = {"$eq": value}

            results = collection.get(
                where=where_clause,
                limit=limit,
                include=["documents", "metadatas", "embeddings"],
            )

            return {
                "filter": metadata_filter,
                "count": len(results["ids"]),
                "documents": [
                    {
                        "id": doc_id,
                        "document": doc,
                        "metadata": meta,
                        "embedding_length": len(emb) if emb else 0,
                    }
                    for doc_id, doc, meta, emb in zip(
                        results["ids"],
                        results["documents"],
                        results["metadatas"],
                        results["embeddings"],
                        strict=False,
                    )
                ],
            }
        except Exception:
            logger.exception(f"Error filtering collection '{collection_name}' by metadata")
            return None

    def explore_collection_structure(self, collection_name: str) -> dict[str, Any] | None:
        """Explore the structure and content of a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection structure information or None if error occurs

        """
        try:
            collection = self.client.get_collection(name=collection_name)

            # Get all documents to analyze structure
            all_docs = collection.get(limit=1000)  # Adjust limit as needed

            if not all_docs["documents"]:
                return {"name": collection_name, "empty": True}

            # Analyze metadata structure
            metadata_keys = set()
            for meta in all_docs["metadatas"]:
                if meta:
                    metadata_keys.update(meta.keys())

            # Analyze document lengths
            doc_lengths = [len(doc) if doc else 0 for doc in all_docs["documents"]]

            # Analyze embedding dimensions
            embedding_dims = [len(emb) if emb else 0 for emb in all_docs["embeddings"]]

            return {
                "name": collection_name,
                "total_documents": len(all_docs["documents"]),
                "metadata_fields": list(metadata_keys),
                "document_length_stats": {
                    "min": min(doc_lengths) if doc_lengths else 0,
                    "max": max(doc_lengths) if doc_lengths else 0,
                    "avg": sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0,
                },
                "embedding_dimension_stats": {
                    "min": min(embedding_dims) if embedding_dims else 0,
                    "max": max(embedding_dims) if embedding_dims else 0,
                    "avg": sum(embedding_dims) / len(embedding_dims) if embedding_dims else 0,
                },
                "sample_documents": all_docs["documents"][:3],  # First 3 documents
                "sample_metadata": all_docs["metadatas"][:3],  # First 3 metadata
            }
        except Exception:
            logger.exception(f"Error exploring collection '{collection_name}'")
            return None

    def export_collection_data(
        self,
        collection_name: str,
        output_file: str,
        file_format: str = "json",
    ) -> bool:
        """Export collection data to a file.

        Args:
            collection_name: Name of the collection
            output_file: Path to output file
            file_format: Export format ("json" or "csv")

        Returns:
            True if successful, False otherwise

        """
        try:
            collection = self.client.get_collection(name=collection_name)
            all_docs = collection.get(limit=10000)  # Adjust limit as needed

            if file_format.lower() == "json":
                with Path(output_file).open("w", encoding="utf-8") as f:
                    json.dump(all_docs, f, indent=2, ensure_ascii=False)
            elif file_format.lower() == "csv":
                import csv

                with Path(output_file).open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(["id", "document", "metadata", "embedding_length"])
                    # Write data
                    for i, doc_id in enumerate(all_docs["ids"]):
                        doc = all_docs["documents"][i] if i < len(all_docs["documents"]) else ""
                        meta = all_docs["metadatas"][i] if i < len(all_docs["metadatas"]) else {}
                        emb_len = len(all_docs["embeddings"][i]) if i < len(all_docs["embeddings"]) else 0
                        writer.writerow([doc_id, doc, json.dumps(meta), emb_len])
            else:
                logger.error(f"Unsupported format: {file_format}")
                return False

            logger.info(f"Successfully exported collection '{collection_name}' to {output_file}")
            return True

        except Exception:
            logger.exception(f"Error exporting collection '{collection_name}'")
            return False

    def close(self) -> None:
        """Close the ChromaDB client connection."""
        # ChromaDB client doesn't need explicit cleanup in newer versions


# Convenience functions for quick queries
def quick_search(db_path: str, collection_name: str, query_text: str, n_results: int = 5) -> None:
    """Quick search function for simple queries.

    Args:
        db_path: Path to ChromaDB database
        collection_name: Name of collection to search
        query_text: Text to search for
        n_results: Number of results to return

    """
    utils = ChromaDBQueryUtils(db_path)
    try:
        results = utils.search_similar_texts(collection_name, query_text, n_results)
        if results:
            logger.info(f"\n🔍 Search Results for: '{query_text}'")
            logger.info(f"Collection: {collection_name}")
            logger.info(f"Results found: {len(results['results'])}\n")

            for result in results["results"]:
                logger.info(f"Rank {result['rank']} (Distance: {result['distance']:.4f})")
                logger.info(f"Document: {result['document'][:200]}{'...' if len(result['document']) > 200 else ''}")
                if result["metadata"]:
                    logger.info(f"Metadata: {result['metadata']}")
                logger.info("-" * 80)
        else:
            logger.info(f"No results found for query: '{query_text}'")
    finally:
        utils.close()


def check_chromadb_connection(db_path: str = "./chroma_db") -> bool:
    """Check if ChromaDB connection is working.

    Args:
        db_path: Path to ChromaDB database

    Returns:
        True if connection works, False otherwise

    """
    try:
        logger.info(f"🔍 Testing ChromaDB connection to: {db_path}")
        path = Path(db_path)

        if not path.exists():
            logger.error(f"❌ Database path does not exist: {db_path}")
            return False

        logger.info(f"✅ Database path exists: {db_path}")

        # Try to create a client
        client = chromadb.PersistentClient(
            path=str(path),
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("✅ ChromaDB client created successfully")

        # Try to list collections
        collections = client.list_collections()
        logger.info(f"✅ Successfully listed collections: {len(collections)} found")

        return True

    except Exception:
        logger.exception("❌ ChromaDB connection failed")
        import traceback

        traceback.print_exc()
        return False


def explore_database(db_path: str = "./chroma_db") -> None:
    """Explore the entire database structure.

    Args:
        db_path: Path to ChromaDB database

    """
    utils = ChromaDBQueryUtils(db_path)
    try:
        collections = utils.list_collections()
        logger.info(f"\n📚 ChromaDB Database: {db_path}")
        logger.info(f"Collections found: {len(collections)}\n")

        for collection_name in collections:
            logger.info(f"🔍 Collection: {collection_name}")
            info = utils.get_collection_info(collection_name)
            if info:
                logger.info(f"   Documents: {info['document_count']}")
                logger.info(f"   Embedding dimension: {info['embedding_dimension']}")
                if info["sample_document"]:
                    sample_text = info["sample_document"][:100]
                    ellipsis = "..." if len(info["sample_document"]) > 100 else ""
                    logger.info(f"   Sample: {sample_text}{ellipsis}")
            logger.info("")
    finally:
        utils.close()


def find_working_collections(db_path: str = "./chroma_db") -> list[str]:
    """Find collections that have working embeddings for queries.

    Args:
        db_path: Path to ChromaDB database

    Returns:
        List of collection names that can be queried

    """
    utils = ChromaDBQueryUtils(db_path)
    working_collections = []

    try:
        collections = utils.list_collections()
        logger.info(f"🔍 Testing {len(collections)} collections for compatibility...")

        for collection_name in collections:
            try:
                # Try to get collection info
                info = utils.get_collection_info(collection_name)
                if info and info["document_count"] > 0 and info["embedding_dimension"] > 0:
                    # Try a simple query to test if it works
                    test_results = utils.search_similar_texts(collection_name, "test", 1)
                    if test_results:
                        working_collections.append(collection_name)
                        doc_count = info["document_count"]
                        embed_dim = info["embedding_dimension"]
                        logger.info(f"✅ {collection_name}: {doc_count} docs, {embed_dim}D")
                    else:
                        logger.warning(f"⚠️  {collection_name}: Has embeddings but query failed")
                else:
                    logger.warning(f"❌ {collection_name}: No documents or embeddings")
            except Exception:
                logger.exception(f"❌ {collection_name}: Error - truncated")

        logger.info(f"\n🎯 Found {len(working_collections)} working collections")
        return working_collections

    finally:
        utils.close()


def test_vector_database_query(db_path: str) -> None:
    """Test function specifically for querying 'what is vector database'.

    Args:
        db_path: Path to ChromaDB database

    """
    logger.info("🔍 Testing ChromaDB Query: 'what is vector database'")
    logger.info("=" * 60)

    # First find working collections
    working_collections = find_working_collections(db_path)

    if not working_collections:
        logger.error("❌ No working collections found. All collections have issues.")
        return

    # Use the first working collection
    collection_name = working_collections[0]
    logger.info(f"\n🎯 Using working collection: {collection_name}")

    utils = ChromaDBQueryUtils(db_path)
    try:
        # Get collection info
        info = utils.get_collection_info(collection_name)
        if info:
            logger.info("📊 Collection info:")
            logger.info(f"   Documents: {info['document_count']}")
            logger.info(f"   Embedding dimension: {info['embedding_dimension']}")

        # Perform the semantic search
        logger.info("\n🔍 Searching for: 'what is vector database'")
        results = utils.search_similar_texts(collection_name, "what is vector database", 5)

        if results and results["results"]:
            logger.info(f"✅ Found {len(results['results'])} results:\n")

            for _i, result in enumerate(results["results"]):
                similarity_score = 1 - result["distance"]
                logger.info(f"🏆 Rank {result['rank']} (Similarity: {similarity_score:.4f})")
                logger.info(f"📄 Document: {result['document'][:200]}{'...' if len(result['document']) > 200 else ''}")

                if result["metadata"]:
                    logger.info(f"🏷️  Metadata: {result['metadata']}")

                logger.info(f"📏 Distance: {result['distance']:.6f}")
                logger.info("-" * 80)
        else:
            logger.warning("❌ No results found for the query")

        # Also test a few related queries
        logger.info("\n🔍 Testing related queries:")
        related_queries = [
            "vector database explanation",
            "how do vector databases work",
            "semantic search with embeddings",
        ]

        for query in related_queries:
            logger.info(f"\n   Query: '{query}'")
            related_results = utils.search_similar_texts(collection_name, query, 2)
            if related_results and related_results["results"]:
                best_match = related_results["results"][0]
                similarity = 1 - best_match["distance"]
                logger.info(f"   Best match: {similarity:.4f} - {best_match['document'][:100]}...")
            else:
                logger.info("   No results found")

    except Exception:
        logger.exception("❌ Error during testing")
    finally:
        utils.close()


def cleanup_empty_collections(db_path: str = "./chroma_db") -> None:
    """Remove empty or problematic collections.

    Args:
        db_path: Path to ChromaDB database

    """
    utils = ChromaDBQueryUtils(db_path)

    try:
        collections = utils.list_collections()
        logger.info(f"🧹 Checking {len(collections)} collections for cleanup...")

        for collection_name in collections:
            try:
                info = utils.get_collection_info(collection_name)
                if info and info["document_count"] == 0:
                    logger.info(f"🗑️  Removing empty collection: {collection_name}")
                    utils.client.delete_collection(name=collection_name)
                elif info and info["embedding_dimension"] == 0:
                    logger.info(f"🗑️  Removing collection with no embeddings: {collection_name}")
                    utils.client.delete_collection(name=collection_name)
            except Exception:
                logger.exception(f"⚠️  Could not check {collection_name}")

        logger.info("🧹 Cleanup completed")

    finally:
        utils.close()


if __name__ == "__main__":
    # Example usage
    logger.info("ChromaDB Query Utilities")
    logger.info("=" * 50)

    # First, check if ChromaDB connection works
    logger.info("\n🔍 Step 0: Testing ChromaDB connection...")
    if not check_chromadb_connection():
        logger.error("❌ ChromaDB connection failed. Cannot proceed.")
        sys.exit(1)

    logger.info("✅ ChromaDB connection successful!")

    # First, find working collections
    logger.info("\n🔍 Step 1: Finding working collections...")
    working_collections = find_working_collections()

    if working_collections:
        logger.info(f"\n✅ Found {len(working_collections)} working collections")

        # Test the specific vector database query
        logger.info("\n🔍 Step 2: Testing vector database query...")
        test_vector_database_query()

        # Explore the database
        logger.info("\n🔍 Step 3: Exploring database structure...")
        explore_database()
    else:
        logger.warning("\n❌ No working collections found. Database may need cleanup.")
        logger.info("🧹 Running cleanup...")
        cleanup_empty_collections()

        # Try to find working collections again
        logger.info("\n🔍 Checking for working collections after cleanup...")
        working_collections = find_working_collections()
        if working_collections:
            logger.info(f"\n✅ Found {len(working_collections)} working collections after cleanup")
            test_vector_database_query()
        else:
            logger.error("❌ Still no working collections. Database may be corrupted.")

    # Example search (uncomment and modify as needed)
    # quick_search("./chroma_db", "documents_20250811_110717", "sample document", 3)
