"""Deployment policy and operational defaults shared by runtime and proof scripts.

These are explicit source defaults, not environment-variable overrides. Changing
an endpoint, delivery target, sandbox boundary or limit still requires the
corresponding authorization and verification. Credential values never belong here.
"""

# Commissioned deployment and repository identity.
COMMISSIONED_SSH_TARGET = 'karell@192.168.1.176'
SERVICE_LOOPBACK_HOST = '127.0.0.1'
SERVICE_PORT = 18080
LOCAL_BIND_HOST = '127.0.0.1'
AUTHORIZED_DELIVERY_REPOSITORY = 'stemarie/context-foundry'
DELIVERY_BRANCH = 'main'
GITHUB_ORIGIN = 'https://github.com'
# Owning source/provenance stays fixed when the delivery target is adapted.
SOURCE_REPOSITORY_URL = 'https://github.com/stemarie/context-foundry'
DELIVERY_REPOSITORY_URL = f'{GITHUB_ORIGIN}/{AUTHORIZED_DELIVERY_REPOSITORY}'
SUPPORTED_CONTRACT_VERSION = 'Alpha 1.0'

# Supported host paths and private filesystem policy.
MACOS_TEMP_DIRECTORY = '/private/tmp'
PS_EXECUTABLE = '/bin/ps'
SANDBOX_EXECUTABLE = '/usr/bin/sandbox-exec'
CHECK_PYTHON_EXECUTABLE = '/Library/Developer/CommandLineTools/usr/bin/python3'
HOOK_PYTHON_EXECUTABLE = '/usr/bin/python3'
RESTRICTED_PATH = '/usr/bin:/bin'
SANDBOX_BACKEND_NAME = 'macos sandbox-exec'
SANDBOX_READ_ROOTS = (
    '/System', '/usr', '/bin', '/sbin', '/Library/Developer/CommandLineTools',
    '/Library/Frameworks/Python3.framework',
)
PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
FORBIDDEN_PRIVATE_PERMISSION_BITS = 0o077

# Runtime timeouts, polling and connection recovery (seconds).
SERVICE_REQUEST_TIMEOUT_SECONDS = 10
SQLITE_BUSY_TIMEOUT_SECONDS = 15
SSH_CONTROL_TIMEOUT_SECONDS = 5
SSH_CONNECT_TIMEOUT_SECONDS = 10
SSH_KEEPALIVE_INTERVAL_SECONDS = 15
SSH_KEEPALIVE_MAX_MISSES = 2
SSH_READY_TIMEOUT_SECONDS = 15
PROCESS_STOP_TIMEOUT_SECONDS = 10
TRANSPORT_TIMEOUT_SECONDS = 90
TRANSPORT_STOP_TIMEOUT_SECONDS = 5
LAUNCH_ACK_TIMEOUT_SECONDS = 90
LAUNCH_POLL_INTERVAL_SECONDS = 0.03
POLL_INTERVAL_SECONDS = 0.05
BREAKER_INITIAL_DELAY_SECONDS = 30
BREAKER_MAX_DELAY_SECONDS = 300
BREAKER_MAX_EXPONENT = 4
CHECK_TIMEOUT_SECONDS = 90

# Service pagination, model-facing output and bounded workspace operations.
TEXT_PAGE_MAX_CHARACTERS = 64000
HISTORY_PAGE_SIZE = 100
ASSIGNMENT_HISTORY_LIMIT = 10
ASSIGNMENT_FILE_LIMIT = 200
CHECK_OUTPUT_MAX_CHARACTERS = 12000
EDIT_MAX_REPLACEMENTS = 64
EDIT_LITERAL_MAX_BYTES = 32768
EDIT_FILE_MAX_BYTES = 512000
WRITE_MAX_BYTES = 128000
HISTORY_SEARCH_LIMIT = 1000
RECOVERY_EVIDENCE_MAX_CHARACTERS = 1024
FAILURE_DIAGNOSTIC_MAX_CHARACTERS = 1000

# Worker invocation defaults and SDK bounds.
DEFAULT_SDK_CONFIG = {'max_iterations': 12, 'max_tokens': 3000, 'run_budget_seconds': 180}
SDK_LIMITS = {'max_iterations': (1, 48), 'max_tokens': (256, 12000), 'run_budget_seconds': (1, 1200)}
DEFAULT_INVOCATION_SECONDS = 600
INVOCATION_MIN_SECONDS = 1
INVOCATION_MAX_SECONDS = 1200
DEFAULT_HEARTBEAT_SECONDS = 5
DEFAULT_LEASE_SECONDS = 300
DEFAULT_START_BARRIER_SECONDS = 120
AUTHORITY_RETRY_SECONDS = 0.5
OWNERSHIP_WAIT_SECONDS = 0.2

# Disposable service fixtures; these do not configure the commissioned service.
FIXTURE_SERVICE_TIMEOUT_SECONDS = 15
ACCEPTANCE_PROVIDER = 'openai-codex'
ACCEPTANCE_MODEL = 'gpt-5.6-terra'
GITHUB_CONNECTION_ALIAS = 'owner-github-context-foundry'
FIXTURE_CONTAINER_PORT = 8080
FIXTURE_CONTAINER_UID = '65532'
FIXTURE_CONTAINER_USER = f'{FIXTURE_CONTAINER_UID}:{FIXTURE_CONTAINER_UID}'
FIXTURE_STATE_DIRECTORY = '/var/lib/ai-contract'
FIXTURE_HELPER_IMAGE = 'busybox:1.36'
FIXTURE_DOCKER_HOST = 'unix:///var/run/docker.sock'
FIXTURE_DOCKER_TIMEOUT_SECONDS = 120
FIXTURE_READY_TIMEOUT_SECONDS = 30
FIXTURE_READY_REQUEST_TIMEOUT_SECONDS = 1
FIXTURE_POLL_INTERVAL_SECONDS = 0.2
FIXTURE_REPLACEMENT_DOWNTIME_SECONDS = 6
