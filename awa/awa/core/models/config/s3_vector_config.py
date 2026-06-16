"""S3 Vector Store configuration models."""

from typing import Literal

from pydantic import BaseModel, Field


class S3VectorConfig(BaseModel):
    """Configuration for S3 Vector Store."""

    enabled: bool = Field(default=False, description="Enable S3 Vector Store")
    region_name: str = Field(default="us-west-2", description="AWS region name")
    vector_bucket_name: str | None = Field(default=None, description="S3 Vector bucket name")
    vector_bucket_arn: str | None = Field(default=None, description="S3 Vector bucket ARN")
    index_name: str = Field(default="awa-vectors", description="Default vector index name")
    distance_metric: Literal["euclidean", "cosine"] = Field(
        default="cosine",
        description="Distance metric for similarity search",
    )
    data_type: Literal["float32"] = Field(default="float32", description="Vector data type")
    embedding_source: Literal["openai", "azure_openai", "tfidf"] = Field(
        default="azure_openai",
        description="Source of embeddings (uses existing LLM config)",
    )
    metadata_keys: list[str] = Field(
        default_factory=lambda: ["source_text", "file_path", "chunk_id", "timestamp", "embedding_model"],
        description="Non-filterable metadata keys",
    )
