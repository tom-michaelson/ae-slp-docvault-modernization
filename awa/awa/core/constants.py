TASK_QUEUE = "awa_default"
TEMPORAL_DB_FILENAME = "temporal.db"
TEMPORAL_NAMESPACE_RETENTION_DAYS = 14

# Worker polling timeout constants
WORKER_POLL_STARTUP_TIMEOUT_SECONDS = 120  # Extended timeout for worker startup
WORKER_POLL_RUNTIME_TIMEOUT_SECONDS = 66  # Normal timeout for runtime monitoring

# Cache
CACHE_DIR = "cache"
CACHE_FILE_EXTENSION = "cache"

# Workflow Behavior
DEFAULT_ACTIVITY_TIMEOUT_SECONDS = 5
DEFAULT_WORKFLOW_TIMEOUT_SECONDS = 30
DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS = 60 * 15
DEFAULT_WORKER_TIMEOUT = 30
WORKER_START_MAX_RETRIES = 3
SERVER_START_MAX_RETRIES = 3

# Worker Polling Timeout Constants (AWA-133 Phase 2.1: Extended Grace Periods)
DEFAULT_WORKER_POLL_RUNTIME_TIMEOUT_SECONDS = 66  # Runtime monitoring timeout
DEFAULT_WORKER_POLL_STARTUP_TIMEOUT_SECONDS = 120  # Extended startup timeout

# Workflow Timeouts
WORKFLOW_BUFFER_MINUTES = 5  # Extra time buffer for setup/cleanup beyond agent execution
WORKFLOW_TASK_TIMEOUT_SECONDS = 30  # Individual workflow task timeout
DEFAULT_AGENT_ACTIVITY_TIMEOUT_SECONDS = 60 * 15
DEFAULT_TRANSFORM_BATCH_MAX_CONCURRENCY = 5

# Inputs
DEFAULT_DIRECTORY_JOIN_STR = "\n"
DEFAULT_DIRECTORY_JOIN_TEMPLATE_STR = '<file name="{file}">\n{content}\n</file>'

# BAML
SCHEMA_PARSER_PAYLOAD_NAME = "payload"

# Logging
MAX_LOG_MESSAGE_SIZE = 1024 * 1024  # 1MB

# Worker Names
CORE_WORKER_NAME = "awa-worker"
