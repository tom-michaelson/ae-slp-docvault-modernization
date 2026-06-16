from enum import StrEnum


class MCPServerTransport(StrEnum):
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


class ResponseFormat(StrEnum):
    TEXT = "text"
    JSON_SCHEMA = "json_schema"
