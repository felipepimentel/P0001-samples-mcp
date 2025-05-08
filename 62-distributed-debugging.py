import getpass
import json
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Handle potential getlogin issues
os.getlogin = getpass.getuser

from mcp.server.fastmcp import FastMCP

# Initialize MCP server for distributed debugging
mcp = FastMCP("Distributed Debugging")

# Directory for storing logs, traces, and analysis results
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_debugging"
LOGS_DIR = DATA_DIR / "logs"
TRACES_DIR = DATA_DIR / "traces"
ANALYSIS_DIR = DATA_DIR / "analysis"
RCA_DIR = DATA_DIR / "root_cause_analysis"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
TRACES_DIR.mkdir(exist_ok=True)
ANALYSIS_DIR.mkdir(exist_ok=True)
RCA_DIR.mkdir(exist_ok=True)


# Define service types for a microservices architecture
class ServiceType(str, Enum):
    API_GATEWAY = "api_gateway"
    AUTH_SERVICE = "auth_service"
    USER_SERVICE = "user_service"
    PAYMENT_SERVICE = "payment_service"
    NOTIFICATION_SERVICE = "notification_service"
    PRODUCT_SERVICE = "product_service"
    ORDER_SERVICE = "order_service"
    INVENTORY_SERVICE = "inventory_service"
    SEARCH_SERVICE = "search_service"
    CACHE_SERVICE = "cache_service"
    DATABASE = "database"


# Define log levels
class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Define trace span types
class SpanType(str, Enum):
    HTTP = "http"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    INTERNAL = "internal"


# Sample services and their dependencies
SERVICE_DEPENDENCIES = {
    ServiceType.API_GATEWAY: [
        ServiceType.AUTH_SERVICE,
        ServiceType.USER_SERVICE,
        ServiceType.PRODUCT_SERVICE,
        ServiceType.ORDER_SERVICE,
        ServiceType.SEARCH_SERVICE,
    ],
    ServiceType.AUTH_SERVICE: [ServiceType.USER_SERVICE, ServiceType.DATABASE],
    ServiceType.USER_SERVICE: [ServiceType.DATABASE, ServiceType.CACHE_SERVICE],
    ServiceType.PAYMENT_SERVICE: [
        ServiceType.USER_SERVICE,
        ServiceType.ORDER_SERVICE,
        ServiceType.DATABASE,
    ],
    ServiceType.NOTIFICATION_SERVICE: [ServiceType.USER_SERVICE, ServiceType.DATABASE],
    ServiceType.PRODUCT_SERVICE: [
        ServiceType.DATABASE,
        ServiceType.CACHE_SERVICE,
        ServiceType.INVENTORY_SERVICE,
    ],
    ServiceType.ORDER_SERVICE: [
        ServiceType.USER_SERVICE,
        ServiceType.PRODUCT_SERVICE,
        ServiceType.PAYMENT_SERVICE,
        ServiceType.INVENTORY_SERVICE,
        ServiceType.DATABASE,
    ],
    ServiceType.INVENTORY_SERVICE: [ServiceType.DATABASE, ServiceType.CACHE_SERVICE],
    ServiceType.SEARCH_SERVICE: [
        ServiceType.PRODUCT_SERVICE,
        ServiceType.CACHE_SERVICE,
    ],
    ServiceType.CACHE_SERVICE: [],
    ServiceType.DATABASE: [],
}

# Sample service latency characteristics (in ms)
SERVICE_LATENCY = {
    ServiceType.API_GATEWAY: {"normal": 10, "degraded": 50, "error": 200},
    ServiceType.AUTH_SERVICE: {"normal": 50, "degraded": 200, "error": 500},
    ServiceType.USER_SERVICE: {"normal": 30, "degraded": 150, "error": 400},
    ServiceType.PAYMENT_SERVICE: {"normal": 100, "degraded": 300, "error": 800},
    ServiceType.NOTIFICATION_SERVICE: {"normal": 20, "degraded": 100, "error": 300},
    ServiceType.PRODUCT_SERVICE: {"normal": 40, "degraded": 180, "error": 450},
    ServiceType.ORDER_SERVICE: {"normal": 60, "degraded": 250, "error": 600},
    ServiceType.INVENTORY_SERVICE: {"normal": 35, "degraded": 170, "error": 420},
    ServiceType.SEARCH_SERVICE: {"normal": 70, "degraded": 280, "error": 650},
    ServiceType.CACHE_SERVICE: {"normal": 5, "degraded": 40, "error": 100},
    ServiceType.DATABASE: {"normal": 25, "degraded": 120, "error": 350},
}

# Sample error types by service
SERVICE_ERROR_TYPES = {
    ServiceType.API_GATEWAY: [
        "rate_limit_exceeded",
        "invalid_request",
        "service_unavailable",
        "timeout",
    ],
    ServiceType.AUTH_SERVICE: [
        "invalid_credentials",
        "token_expired",
        "user_not_found",
        "unauthorized",
    ],
    ServiceType.USER_SERVICE: [
        "user_not_found",
        "validation_error",
        "database_error",
        "cache_miss",
    ],
    ServiceType.PAYMENT_SERVICE: [
        "payment_declined",
        "invalid_card",
        "insufficient_funds",
        "timeout",
    ],
    ServiceType.NOTIFICATION_SERVICE: [
        "delivery_failed",
        "invalid_recipient",
        "template_error",
        "rate_limit_exceeded",
    ],
    ServiceType.PRODUCT_SERVICE: [
        "product_not_found",
        "invalid_category",
        "database_error",
        "cache_miss",
    ],
    ServiceType.ORDER_SERVICE: [
        "inventory_insufficient",
        "payment_failed",
        "validation_error",
        "user_not_found",
    ],
    ServiceType.INVENTORY_SERVICE: [
        "stock_unavailable",
        "database_error",
        "cache_miss",
        "update_conflict",
    ],
    ServiceType.SEARCH_SERVICE: [
        "query_timeout",
        "index_error",
        "service_overloaded",
        "invalid_query",
    ],
    ServiceType.CACHE_SERVICE: [
        "cache_miss",
        "eviction",
        "memory_limit",
        "connection_error",
    ],
    ServiceType.DATABASE: [
        "query_timeout",
        "connection_failed",
        "deadlock",
        "constraint_violation",
        "disk_full",
    ],
}

# Common error patterns that can occur in a distributed system
COMMON_ERROR_PATTERNS = [
    {
        "name": "Cascading Timeouts",
        "description": "A slow database causes timeouts in dependent services, eventually affecting the entire system",
        "root_cause": "Database overload or query inefficiency",
        "symptom_pattern": "Timeouts starting in database service, then propagating to dependent services",
        "fix_suggestion": "Optimize slow queries, add indexes, or scale up database resources",
    },
    {
        "name": "Cache Inconsistency",
        "description": "Cached data becomes inconsistent with the database, leading to incorrect results",
        "root_cause": "Cache invalidation failure or race condition",
        "symptom_pattern": "Inconsistent data reported between cache reads and database reads",
        "fix_suggestion": "Implement proper cache invalidation or use cache-aside pattern",
    },
    {
        "name": "Network Partition",
        "description": "Services unable to communicate due to network issues",
        "root_cause": "Infrastructure failure or configuration error",
        "symptom_pattern": "Connection errors between specific services",
        "fix_suggestion": "Check network infrastructure, improve resilience with circuit breakers",
    },
    {
        "name": "Authentication Failure",
        "description": "Users unable to authenticate or services reject valid credentials",
        "root_cause": "Expired certificates, clock drift, or token validation issues",
        "symptom_pattern": "Authentication errors across multiple services",
        "fix_suggestion": "Check certificate expiration, synchronize clocks, verify token validation logic",
    },
    {
        "name": "Resource Exhaustion",
        "description": "Service becomes unavailable due to running out of resources",
        "root_cause": "Memory leak, connection pool exhaustion, or thread starvation",
        "symptom_pattern": "Increasing error rates and latency until service fails",
        "fix_suggestion": "Identify resource leak, increase limits, or implement backpressure mechanisms",
    },
    {
        "name": "Data Corruption",
        "description": "Invalid data propagates through the system causing errors",
        "root_cause": "Bug in data validation or processing logic",
        "symptom_pattern": "Validation errors or unexpected exceptions with specific data payloads",
        "fix_suggestion": "Add data validation at service boundaries, fix processing logic bugs",
    },
    {
        "name": "Circular Dependency",
        "description": "Services unable to start or function properly due to circular initialization",
        "root_cause": "Architectural design flaw",
        "symptom_pattern": "Services repeatedly restarting or timing out during initialization",
        "fix_suggestion": "Redesign service dependencies, implement timeout with fallback",
    },
    {
        "name": "Thundering Herd",
        "description": "Cache expiration causes a flood of requests to a backend service",
        "root_cause": "Multiple cache entries expiring simultaneously",
        "symptom_pattern": "Sudden spike in traffic to specific service after cache timeout",
        "fix_suggestion": "Implement cache jitter, use cache-aside pattern, or stagger expirations",
    },
]


# Helper functions for log and trace generation
def generate_log_entry(
    service: ServiceType,
    level: LogLevel,
    message: str,
    context: Dict[str, Any] = None,
    timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Generate a log entry for a microservice"""
    if timestamp is None:
        timestamp = datetime.now()

    if context is None:
        context = {}

    return {
        "timestamp": timestamp.isoformat(),
        "service": service,
        "level": level,
        "message": message,
        "context": context,
        "host": f"{service}-{uuid.uuid4().hex[:8]}.example.com",
        "environment": "production",
    }


def generate_trace_span(
    trace_id: str,
    span_id: str,
    parent_span_id: Optional[str],
    service: ServiceType,
    operation: str,
    span_type: SpanType,
    start_time: datetime,
    duration_ms: int,
    status: str = "success",
    error: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a trace span for a distributed tracing system"""
    if tags is None:
        tags = {}

    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "service": service,
        "operation": operation,
        "span_type": span_type,
        "start_time": start_time.isoformat(),
        "end_time": (start_time + timedelta(milliseconds=duration_ms)).isoformat(),
        "duration_ms": duration_ms,
        "status": status,
        "error": error,
        "tags": tags,
    }


def save_log_entries(logs: List[Dict[str, Any]], scenario_id: str) -> str:
    """Save a list of log entries to a file"""
    file_path = LOGS_DIR / f"{scenario_id}.json"
    with open(file_path, "w") as f:
        json.dump(logs, f, indent=2)
    return str(file_path)


def save_trace_spans(spans: List[Dict[str, Any]], scenario_id: str) -> str:
    """Save a list of trace spans to a file"""
    file_path = TRACES_DIR / f"{scenario_id}.json"
    with open(file_path, "w") as f:
        json.dump(spans, f, indent=2)
    return str(file_path)


def save_analysis_result(analysis: Dict[str, Any], scenario_id: str) -> str:
    """Save an analysis result to a file"""
    file_path = ANALYSIS_DIR / f"{scenario_id}.json"
    with open(file_path, "w") as f:
        json.dump(analysis, f, indent=2)
    return str(file_path)


def save_root_cause_analysis(rca: Dict[str, Any], scenario_id: str) -> str:
    """Save a root cause analysis to a file"""
    file_path = RCA_DIR / f"{scenario_id}.json"
    with open(file_path, "w") as f:
        json.dump(rca, f, indent=2)
    return str(file_path)
