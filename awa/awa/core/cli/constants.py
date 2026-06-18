INTRO = "----- Slalom Agentic Workflow Accelerator (AWA) -----"

SERVICE_TEMPORAL_SERVER = "temporal_server"
SERVICE_TEMPORAL_WORKER = "temporal_worker"
SERVICE_API = "api"
SERVICE_UI = "ui"

# State file paths
LOCAL_STATE_DIR = ".awa_state"
LOCAL_STATE_FILE = "services.json"

# List of all available services
ALL_SERVICES = [SERVICE_API, SERVICE_UI, SERVICE_TEMPORAL_SERVER, SERVICE_TEMPORAL_WORKER]

# Helper string for help text
SERVICES_HELP_LIST = f"Available services: {', '.join(ALL_SERVICES)}"

# Warning message for UI not supported in package mode
UI_PACKAGE_MODE_WARNING = "UI not supported in package mode."

# Process Management Constants
# Process discovery and validation
MIN_PS_OUTPUT_FIELDS = 2
MIN_PS_PARTS_FOR_ARGS = 3
MIN_WMIC_CSV_PARTS = 3  # Minimum parts for WMIC CSV parsing
MIN_TASKLIST_CSV_PARTS = 2  # Minimum parts for tasklist CSV parsing
MAX_TASKLIST_CSV_PARTS = 8  # Maximum expected parts in tasklist CSV

# Process termination timeouts
PROCESS_TERMINATION_TIMEOUT = 12.0  # Main process termination timeout in seconds
VERIFICATION_TIMEOUT_EXTENDED = 15.0  # Extended timeout for verification
VERIFICATION_TIMEOUT_DEFAULT = 10.0  # Default verification timeout
GRACEFUL_TERMINATION_TIMEOUT = 8.0  # Graceful termination timeout
VERIFICATION_TIMEOUT_FINAL = 5.0  # Final verification timeout

# Process termination retry and backoff
MAX_VERIFICATION_ATTEMPTS = 5  # Maximum verification attempts
VERIFICATION_BACKOFF_INITIAL = 0.5  # Initial backoff delay
VERIFICATION_BACKOFF_MULTIPLIER = 1.5  # Exponential backoff multiplier
MAX_TERMINATION_RETRIES = 3  # Maximum retries for termination verification

# Process command timeouts
COMMAND_TIMEOUT_SHORT = 3  # Short command timeout in seconds
COMMAND_TIMEOUT_STANDARD = 5  # Standard command timeout in seconds
COMMAND_TIMEOUT_MEDIUM = 8  # Medium command timeout in seconds
COMMAND_TIMEOUT_LONG = 10  # Long command timeout in seconds
COMMAND_TIMEOUT_EXTENDED = 15  # Extended command timeout in seconds

# Process discovery limits
MAX_PROCESS_TREE_DEPTH = 50  # Maximum depth for recursive process tree discovery
PROCESS_CHECK_INTERVAL = 0.3  # Interval between process checks in seconds

# Process group and cleanup delays
PROCESS_GROUP_TERMINATION_DELAY = 2.0  # Delay after process group termination
GRACEFUL_TERMINATION_DELAY = 2.0  # Delay for graceful termination
FINAL_CLEANUP_DELAY = 0.5  # Brief delay for signal effects
RETRY_DELAY = 1.0  # Delay between retries

# Stop operation constants (from stop.py)
DEFAULT_STOP_TIMEOUT = 90.0  # Total stop operation timeout in seconds (increased for Windows)
DEFAULT_RETRY_ATTEMPTS = 3  # Maximum retry attempts for stubborn processes
RETRY_BACKOFF_BASE = 1.5  # Exponential backoff multiplier for retries
STOP_VERIFICATION_TIMEOUT = 10.0  # Default stop verification timeout

# Minimum safe process group IDs
MIN_SAFE_PROCESS_GROUP = 1  # Minimum safe process group to terminate

# Process parsing constants
PS_ARGS_FIELD_INDEX = 5  # Index where arguments start in ps output (Linux)
PS_ARGS_FIELD_INDEX_MACOS = 4  # Index where arguments start in ps output (macOS)
PS_COMM_FIELD_INDEX = 2  # Index where command starts in basic ps output
MIN_PS_BASIC_FIELDS = 2  # Minimum fields required for basic ps parsing
