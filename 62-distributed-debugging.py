import getpass
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Handle potential getlogin issues
os.getlogin = getpass.getuser

from mcp.server.fastmcp import FastMCP

# Initialize MCP server for distributed debugging
mcp = FastMCP("Distributed Debugging for Microservices")

# Directory for storing logs and debugging data
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_distributed_debugging"
LOGS_DIR = DATA_DIR / "logs"
TRACES_DIR = DATA_DIR / "traces"
DASHBOARDS_DIR = DATA_DIR / "dashboards"
REPORTS_DIR = DATA_DIR / "reports"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
TRACES_DIR.mkdir(exist_ok=True)
DASHBOARDS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


# Define service types for the microservices architecture
class ServiceType(str, Enum):
    API_GATEWAY = "api_gateway"
    AUTH_SERVICE = "auth_service"
    USER_SERVICE = "user_service"
    PAYMENT_SERVICE = "payment_service"
    NOTIFICATION_SERVICE = "notification_service"
    ORDER_SERVICE = "order_service"
    PRODUCT_SERVICE = "product_service"
    INVENTORY_SERVICE = "inventory_service"
    ANALYTICS_SERVICE = "analytics_service"
    DATABASE = "database"


# Define log levels
class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Define common error patterns
class ErrorPattern(str, Enum):
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INTERNAL_ERROR = "internal_error"


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


# Helper function to generate a realistic log entry
def generate_log_entry(
    service: ServiceType,
    level: LogLevel,
    message: str,
    timestamp: Optional[datetime] = None,
    error_pattern: Optional[ErrorPattern] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    additional_data: Optional[Dict] = None,
) -> Dict:
    """Generate a realistic log entry for a microservice"""
    if timestamp is None:
        timestamp = datetime.now()

    if request_id is None:
        request_id = str(uuid.uuid4())

    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    log_entry = {
        "timestamp": timestamp.isoformat(),
        "service": service,
        "level": level,
        "message": message,
        "request_id": request_id,
        "correlation_id": correlation_id,
    }

    if error_pattern:
        log_entry["error_pattern"] = error_pattern

    if user_id:
        log_entry["user_id"] = user_id

    if additional_data:
        log_entry["data"] = additional_data

    return log_entry


# Helper function to generate a trace span
def generate_trace_span(
    service: ServiceType,
    operation: str,
    parent_span_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    duration_ms: Optional[int] = None,
    status: str = "success",
    error_pattern: Optional[ErrorPattern] = None,
    tags: Optional[Dict] = None,
) -> Dict:
    """Generate a trace span for distributed tracing"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    span_id = str(uuid.uuid4())

    if start_time is None:
        start_time = datetime.now()

    if duration_ms is None:
        duration_ms = random.randint(5, 2000)

    end_time = start_time + timedelta(milliseconds=duration_ms)

    span = {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "service": service,
        "operation": operation,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_ms": duration_ms,
        "status": status,
    }

    if error_pattern:
        span["error_pattern"] = error_pattern
        span["status"] = "error"

    if tags:
        span["tags"] = tags

    return span


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
    file_path = DASHBOARDS_DIR / f"{scenario_id}.json"
    with open(file_path, "w") as f:
        json.dump(analysis, f, indent=2)
    return str(file_path)


def save_root_cause_analysis(rca: Dict[str, Any], scenario_id: str) -> str:
    """Save a root cause analysis to a file"""
    file_path = REPORTS_DIR / f"{scenario_id}.json"
    with open(file_path, "w") as f:
        json.dump(rca, f, indent=2)
    return str(file_path)


def generate_cascading_failure_scenario() -> Dict:
    """
    Generate a scenario that simulates a cascading failure in the system
    """
    scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
    now = datetime.now()
    correlation_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    user_id = f"user_{random.randint(1000, 9999)}"
    
    # Start with a database issue
    logs = []
    traces = []
    
    # Database slowdown
    db_span = generate_trace_span(
        service=ServiceType.DATABASE,
        operation="execute_query",
        trace_id=correlation_id,
        start_time=now,
        duration_ms=800,  # Very slow query
        status="error",
        error_pattern=ErrorPattern.TIMEOUT,
        tags={"query_type": "SELECT", "table": "orders"}
    )
    traces.append(db_span)
    
    logs.append(generate_log_entry(
        service=ServiceType.DATABASE,
        level=LogLevel.ERROR,
        message="Query execution exceeded timeout threshold",
        timestamp=now,
        error_pattern=ErrorPattern.TIMEOUT,
        request_id=request_id,
        correlation_id=correlation_id,
        additional_data={"query_id": "q-123456", "timeout_ms": 500}
    ))
    
    # Order service affected
    now = now + timedelta(milliseconds=50)
    order_span = generate_trace_span(
        service=ServiceType.ORDER_SERVICE,
        operation="get_order_details",
        parent_span_id=db_span["span_id"],
        trace_id=correlation_id,
        start_time=now - timedelta(milliseconds=200),
        duration_ms=900,
        status="error",
        error_pattern=ErrorPattern.TIMEOUT,
        tags={"order_id": "ORD-9876"}
    )
    traces.append(order_span)
    
    logs.append(generate_log_entry(
        service=ServiceType.ORDER_SERVICE,
        level=LogLevel.ERROR,
        message="Failed to fetch order details: database timeout",
        timestamp=now,
        error_pattern=ErrorPattern.TIMEOUT,
        request_id=request_id,
        correlation_id=correlation_id,
        user_id=user_id,
        additional_data={"order_id": "ORD-9876"}
    ))
    
    # API Gateway affected
    now = now + timedelta(milliseconds=100)
    api_span = generate_trace_span(
        service=ServiceType.API_GATEWAY,
        operation="GET /api/orders/{id}",
        parent_span_id=order_span["span_id"],
        trace_id=correlation_id,
        start_time=now - timedelta(milliseconds=1000),
        duration_ms=1100,
        status="error",
        error_pattern=ErrorPattern.SERVICE_UNAVAILABLE,
        tags={"http_method": "GET", "endpoint": "/api/orders/ORD-9876"}
    )
    traces.append(api_span)
    
    logs.append(generate_log_entry(
        service=ServiceType.API_GATEWAY,
        level=LogLevel.ERROR,
        message="HTTP 503 Service Unavailable returned to client",
        timestamp=now,
        error_pattern=ErrorPattern.SERVICE_UNAVAILABLE,
        request_id=request_id,
        correlation_id=correlation_id,
        user_id=user_id,
        additional_data={"status_code": 503, "endpoint": "/api/orders/ORD-9876"}
    ))
    
    # User service also impacted (shared database connection pool)
    now = now + timedelta(milliseconds=150)
    user_span = generate_trace_span(
        service=ServiceType.USER_SERVICE,
        operation="get_user_profile",
        trace_id=str(uuid.uuid4()),  # Different trace
        start_time=now,
        duration_ms=750,
        status="error",
        error_pattern=ErrorPattern.DATABASE_ERROR,
        tags={"user_id": "USR-1234"}
    )
    traces.append(user_span)
    
    logs.append(generate_log_entry(
        service=ServiceType.USER_SERVICE,
        level=LogLevel.ERROR,
        message="Database connection pool exhausted",
        timestamp=now,
        error_pattern=ErrorPattern.DATABASE_ERROR,
        request_id=str(uuid.uuid4()),  # Different request
        correlation_id=user_span["trace_id"],
        additional_data={"pool_size": 20, "active_connections": 20}
    ))
    
    # Save scenario data
    logs_path = save_log_entries(logs, scenario_id)
    traces_path = save_trace_spans(traces, scenario_id)
    
    return {
        "scenario_id": scenario_id,
        "name": "Cascading Database Failure",
        "logs_path": logs_path,
        "traces_path": traces_path,
        "timestamp": now.isoformat(),
        "correlation_id": correlation_id,
        "affected_services": [
            ServiceType.DATABASE,
            ServiceType.ORDER_SERVICE,
            ServiceType.API_GATEWAY,
            ServiceType.USER_SERVICE
        ]
    }


def generate_authentication_failure_scenario() -> Dict:
    """
    Generate a scenario that simulates authentication service failures
    """
    scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
    now = datetime.now()
    correlation_id = str(uuid.uuid4())
    
    logs = []
    traces = []
    
    # Auth service certificate expired
    auth_span = generate_trace_span(
        service=ServiceType.AUTH_SERVICE,
        operation="validate_token",
        trace_id=correlation_id,
        start_time=now,
        duration_ms=120,
        status="error",
        error_pattern=ErrorPattern.AUTHENTICATION_FAILURE,
        tags={"token_type": "JWT"}
    )
    traces.append(auth_span)
    
    logs.append(generate_log_entry(
        service=ServiceType.AUTH_SERVICE,
        level=LogLevel.CRITICAL,
        message="TLS certificate expired for token signing key",
        timestamp=now,
        error_pattern=ErrorPattern.AUTHENTICATION_FAILURE,
        correlation_id=correlation_id,
        additional_data={"cert_expiry": (now - timedelta(hours=2)).isoformat(), "key_id": "sig-key-1"}
    ))
    
    # Multiple failed authentications across services
    for i in range(5):
        now = now + timedelta(seconds=random.randint(5, 15))
        user_id = f"user_{random.randint(1000, 9999)}"
        request_id = str(uuid.uuid4())
        
        # API Gateway auth failure
        api_span = generate_trace_span(
            service=ServiceType.API_GATEWAY,
            operation=f"authenticate_request_{i}",
            parent_span_id=auth_span["span_id"],
            trace_id=correlation_id,
            start_time=now - timedelta(milliseconds=50),
            duration_ms=200,
            status="error",
            error_pattern=ErrorPattern.AUTHENTICATION_FAILURE,
            tags={"endpoint": f"/api/resources/{i}", "auth_method": "bearer"}
        )
        traces.append(api_span)
        
        logs.append(generate_log_entry(
            service=ServiceType.API_GATEWAY,
            level=LogLevel.ERROR,
            message=f"Authentication failed for request to /api/resources/{i}",
            timestamp=now,
            error_pattern=ErrorPattern.AUTHENTICATION_FAILURE,
            request_id=request_id,
            correlation_id=correlation_id,
            user_id=user_id,
            additional_data={"token_validation_error": "signature verification failed"}
        ))
    
    # Auth service logs additional context
    now = now + timedelta(seconds=5)
    logs.append(generate_log_entry(
        service=ServiceType.AUTH_SERVICE,
        level=LogLevel.CRITICAL,
        message="Multiple token validation failures detected in last 5 minutes",
        timestamp=now,
        error_pattern=ErrorPattern.AUTHENTICATION_FAILURE,
        correlation_id=correlation_id,
        additional_data={"failure_count": 27, "unique_users": 18}
    ))
    
    # Save scenario data
    logs_path = save_log_entries(logs, scenario_id)
    traces_path = save_trace_spans(traces, scenario_id)
    
    return {
        "scenario_id": scenario_id,
        "name": "Authentication Service Failure",
        "logs_path": logs_path,
        "traces_path": traces_path,
        "timestamp": now.isoformat(),
        "correlation_id": correlation_id,
        "affected_services": [
            ServiceType.AUTH_SERVICE,
            ServiceType.API_GATEWAY
        ]
    }


def generate_network_partition_scenario() -> Dict:
    """
    Generate a scenario that simulates network partition between services
    """
    scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
    now = datetime.now()
    correlation_id = str(uuid.uuid4())
    
    logs = []
    traces = []
    
    # Network partition between services
    affected_pairs = [
        (ServiceType.ORDER_SERVICE, ServiceType.PAYMENT_SERVICE),
        (ServiceType.ORDER_SERVICE, ServiceType.INVENTORY_SERVICE),
        (ServiceType.API_GATEWAY, ServiceType.ORDER_SERVICE)
    ]
    
    for source, target in affected_pairs:
        request_id = str(uuid.uuid4())
        
        source_span = generate_trace_span(
            service=source,
            operation=f"request_to_{target}",
            trace_id=correlation_id,
            start_time=now,
            duration_ms=3000,  # Timeout after 3 seconds
            status="error",
            error_pattern=ErrorPattern.NETWORK_ERROR,
            tags={"target_service": target}
        )
        traces.append(source_span)
        
        logs.append(generate_log_entry(
            service=source,
            level=LogLevel.ERROR,
            message=f"Connection failed to {target}: connection refused",
            timestamp=now,
            error_pattern=ErrorPattern.NETWORK_ERROR,
            request_id=request_id,
            correlation_id=correlation_id,
            additional_data={"target_service": target, "retry_count": 3}
        ))
        
        now = now + timedelta(seconds=random.randint(1, 3))
    
    # Infrastructure logs showing network issues
    now = now + timedelta(seconds=5)
    logs.append(generate_log_entry(
        service="infrastructure",
        level=LogLevel.CRITICAL,
        message="Network partition detected in zone us-east-1c",
        timestamp=now,
        error_pattern=ErrorPattern.NETWORK_ERROR,
        correlation_id=correlation_id,
        additional_data={"affected_zone": "us-east-1c", "duration_s": 120}
    ))
    
    # Save scenario data
    logs_path = save_log_entries(logs, scenario_id)
    traces_path = save_trace_spans(traces, scenario_id)
    
    return {
        "scenario_id": scenario_id,
        "name": "Network Partition",
        "logs_path": logs_path,
        "traces_path": traces_path,
        "timestamp": now.isoformat(),
        "correlation_id": correlation_id,
        "affected_services": [
            ServiceType.ORDER_SERVICE,
            ServiceType.PAYMENT_SERVICE,
            ServiceType.INVENTORY_SERVICE,
            ServiceType.API_GATEWAY
        ]
    }


# Create a list of available debugging scenarios
DEBUGGING_SCENARIOS = [
    generate_cascading_failure_scenario(),
    generate_authentication_failure_scenario(),
    generate_network_partition_scenario()
]


# Define MCP Tools for distributed debugging
@mcp.tool
def list_debug_scenarios() -> List[Dict]:
    """
    Lists all available debugging scenarios in the system.
    
    Returns:
        List of debugging scenarios with their ID, name, affected services, and timestamp.
    """
    return [{
        "scenario_id": scenario["scenario_id"],
        "name": scenario["name"],
        "timestamp": scenario["timestamp"],
        "affected_services": scenario["affected_services"]
    } for scenario in DEBUGGING_SCENARIOS]


@mcp.tool
def get_scenario_logs(scenario_id: str) -> List[Dict]:
    """
    Get all logs for a specific debugging scenario.
    
    Args:
        scenario_id: The ID of the scenario to retrieve logs for
        
    Returns:
        List of log entries for the scenario
    """
    for scenario in DEBUGGING_SCENARIOS:
        if scenario["scenario_id"] == scenario_id:
            with open(scenario["logs_path"], "r") as f:
                return json.load(f)
    
    return []


@mcp.tool
def get_scenario_traces(scenario_id: str) -> List[Dict]:
    """
    Get all distributed traces for a specific debugging scenario.
    
    Args:
        scenario_id: The ID of the scenario to retrieve traces for
        
    Returns:
        List of trace spans for the scenario
    """
    for scenario in DEBUGGING_SCENARIOS:
        if scenario["scenario_id"] == scenario_id:
            with open(scenario["traces_path"], "r") as f:
                return json.load(f)
    
    return []


@mcp.tool
def analyze_service_dependencies(scenario_id: str) -> Dict:
    """
    Analyze service dependencies and identify potential cascading failure paths.
    
    Args:
        scenario_id: The ID of the scenario to analyze
        
    Returns:
        Analysis of service dependencies and potential failure paths
    """
    # Get scenario data
    logs = get_scenario_logs(scenario_id)
    traces = get_scenario_traces(scenario_id)
    
    # Extract services involved in the scenario
    services_involved = set()
    for log in logs:
        services_involved.add(log.get("service"))
    
    for trace in traces:
        services_involved.add(trace.get("service"))
    
    # Analyze dependencies
    dependencies = {}
    for service in services_involved:
        if service in SERVICE_DEPENDENCIES:
            dependencies[service] = SERVICE_DEPENDENCIES[service]
    
    # Identify critical paths
    critical_services = []
    for service, deps in dependencies.items():
        dependent_count = sum(1 for s, d in dependencies.items() if service in d)
        if dependent_count > 1:
            critical_services.append({
                "service": service, 
                "dependent_services": dependent_count,
                "dependencies": len(deps)
            })
    
    # Identify potential bottlenecks
    bottlenecks = []
    service_error_counts = {}
    
    for log in logs:
        service = log.get("service")
        if log.get("level") in [LogLevel.ERROR, LogLevel.CRITICAL]:
            service_error_counts[service] = service_error_counts.get(service, 0) + 1
    
    for service, error_count in service_error_counts.items():
        if error_count > 1:
            bottlenecks.append({
                "service": service,
                "error_count": error_count
            })
    
    analysis_result = {
        "scenario_id": scenario_id,
        "services_involved": list(services_involved),
        "service_dependencies": dependencies,
        "critical_services": critical_services,
        "potential_bottlenecks": bottlenecks
    }
    
    save_analysis_result(analysis_result, scenario_id)
    return analysis_result


@mcp.tool
def identify_root_cause(scenario_id: str) -> Dict:
    """
    Perform root cause analysis on a debugging scenario.
    
    Args:
        scenario_id: The ID of the scenario to analyze
        
    Returns:
        Root cause analysis results
    """
    # Get scenario data
    logs = get_scenario_logs(scenario_id)
    traces = get_scenario_traces(scenario_id)
    
    # Sort logs and traces by timestamp
    logs = sorted(logs, key=lambda x: x.get("timestamp", ""))
    traces = sorted(traces, key=lambda x: x.get("start_time", ""))
    
    # Find the earliest error
    earliest_error_log = None
    for log in logs:
        if log.get("level") in [LogLevel.ERROR, LogLevel.CRITICAL]:
            earliest_error_log = log
            break
    
    earliest_error_trace = None
    for trace in traces:
        if trace.get("status") == "error":
            earliest_error_trace = trace
            break
    
    # Identify common error patterns
    error_patterns = {}
    for log in logs:
        error_pattern = log.get("error_pattern")
        if error_pattern:
            error_patterns[error_pattern] = error_patterns.get(error_pattern, 0) + 1
    
    most_common_error = max(error_patterns.items(), key=lambda x: x[1]) if error_patterns else (None, 0)
    
    # Match against known error patterns
    matching_patterns = []
    for pattern in COMMON_ERROR_PATTERNS:
        if earliest_error_log and pattern["symptom_pattern"].lower() in earliest_error_log.get("message", "").lower():
            matching_patterns.append(pattern)
        elif most_common_error[0] and most_common_error[0].lower() in pattern["name"].lower():
            matching_patterns.append(pattern)
    
    # Build the root cause analysis
    root_cause = {
        "scenario_id": scenario_id,
        "most_likely_root_cause": matching_patterns[0] if matching_patterns else None,
        "first_error": {
            "service": earliest_error_log.get("service") if earliest_error_log else None,
            "message": earliest_error_log.get("message") if earliest_error_log else None,
            "timestamp": earliest_error_log.get("timestamp") if earliest_error_log else None,
            "error_pattern": earliest_error_log.get("error_pattern") if earliest_error_log else None,
        },
        "error_distribution": error_patterns,
        "possible_causes": matching_patterns,
        "recommended_fixes": [pattern["fix_suggestion"] for pattern in matching_patterns] if matching_patterns else []
    }
    
    save_root_cause_analysis(root_cause, scenario_id)
    return root_cause


@mcp.tool
def generate_service_diagram(scenario_id: str) -> str:
    """
    Generate a text-based service diagram showing the dependencies and affected services.
    
    Args:
        scenario_id: The ID of the scenario to visualize
        
    Returns:
        Text-based diagram of service dependencies
    """
    # Get scenario data
    analysis = None
    for scenario in DEBUGGING_SCENARIOS:
        if scenario["scenario_id"] == scenario_id:
            try:
                with open(DASHBOARDS_DIR / f"{scenario_id}.json", "r") as f:
                    analysis = json.load(f)
            except FileNotFoundError:
                # Generate analysis if not available
                analysis = analyze_service_dependencies(scenario_id)
            break
    
    if not analysis:
        return "Scenario not found"
    
    # Create a text-based visualization
    diagram = ["Service Dependency Diagram:", ""]
    
    # Add affected services in diagram format
    for service in analysis["services_involved"]:
        if service in analysis["service_dependencies"]:
            dependencies = analysis["service_dependencies"][service]
            diagram.append(f"{service}")
            for dependency in dependencies:
                if dependency in analysis["services_involved"]:
                    diagram.append(f"  └─> {dependency}")
                    
                    # Mark bottlenecks
                    for bottleneck in analysis.get("potential_bottlenecks", []):
                        if bottleneck["service"] == dependency:
                            diagram[-1] += f" [BOTTLENECK: {bottleneck['error_count']} errors]"
    
    return "\n".join(diagram)


@mcp.tool
def create_debug_report(scenario_id: str) -> Dict:
    """
    Create a comprehensive debug report for a scenario.
    
    Args:
        scenario_id: The ID of the scenario to create a report for
        
    Returns:
        Complete debug report with timeline, root cause, and recommendations
    """
    # Get all relevant data
    logs = get_scenario_logs(scenario_id)
    traces = get_scenario_traces(scenario_id)
    
    try:
        with open(REPORTS_DIR / f"{scenario_id}.json", "r") as f:
            root_cause = json.load(f)
    except FileNotFoundError:
        root_cause = identify_root_cause(scenario_id)
        
    try:
        with open(DASHBOARDS_DIR / f"{scenario_id}.json", "r") as f:
            analysis = json.load(f)
    except FileNotFoundError:
        analysis = analyze_service_dependencies(scenario_id)
    
    # Sort logs and traces by timestamp
    logs = sorted(logs, key=lambda x: x.get("timestamp", ""))
    traces = sorted(traces, key=lambda x: x.get("start_time", ""))
    
    # Create a timeline of events
    timeline = []
    for log in logs:
        timeline.append({
            "timestamp": log.get("timestamp"),
            "service": log.get("service"),
            "event_type": "log",
            "level": log.get("level"),
            "message": log.get("message")
        })
    
    for trace in traces:
        timeline.append({
            "timestamp": trace.get("start_time"),
            "service": trace.get("service"),
            "event_type": "trace_start",
            "operation": trace.get("operation"),
            "status": trace.get("status")
        })
        timeline.append({
            "timestamp": trace.get("end_time"),
            "service": trace.get("service"),
            "event_type": "trace_end",
            "operation": trace.get("operation"),
            "duration_ms": trace.get("duration_ms"),
            "status": trace.get("status")
        })
    
    # Sort the combined timeline
    timeline = sorted(timeline, key=lambda x: x.get("timestamp", ""))
    
    # Build the report
    report = {
        "scenario_id": scenario_id,
        "generated_at": datetime.now().isoformat(),
        "timeline": timeline,
        "root_cause_analysis": root_cause,
        "service_dependencies": analysis.get("service_dependencies", {}),
        "critical_services": analysis.get("critical_services", []),
        "potential_bottlenecks": analysis.get("potential_bottlenecks", []),
        "recommendations": root_cause.get("recommended_fixes", []),
        "diagram": generate_service_diagram(scenario_id)
    }
    
    # Find a matching scenario
    for scenario in DEBUGGING_SCENARIOS:
        if scenario["scenario_id"] == scenario_id:
            report["scenario_name"] = scenario["name"]
            report["affected_services"] = scenario["affected_services"]
            break
    
    return report

# Define the prompt for the distributed debugging interface
debug_prompt = """
# Distributed Debugging Assistant

You are an expert distributed systems debugging assistant that helps developers diagnose and fix issues across microservices architectures.

Your capabilities include:
- Analyzing logs and traces from multiple services
- Identifying root causes of failures across distributed systems
- Visualizing service dependencies and failure propagation
- Creating comprehensive debug reports

## Available Tools

- `list_debug_scenarios()` - List all available debugging scenarios
- `get_scenario_logs(scenario_id)` - Get all logs for a specific scenario
- `get_scenario_traces(scenario_id)` - Get all distributed traces for a scenario
- `analyze_service_dependencies(scenario_id)` - Analyze service dependencies and identify failure paths
- `identify_root_cause(scenario_id)` - Perform root cause analysis on a debugging scenario
- `generate_service_diagram(scenario_id)` - Generate a text-based service diagram
- `create_debug_report(scenario_id)` - Create a comprehensive debug report

## Debugging Approach

When debugging distributed systems, follow these steps:
1. Review logs and traces from affected services
2. Look for the earliest errors in the timeline
3. Identify patterns of cascading failures
4. Analyze service dependencies to understand impact
5. Consider common distributed system failure patterns
6. Recommend targeted fixes for the root cause

Remember that many distributed system issues involve subtle interactions between services, timing problems, or resource constraints that may not be obvious from a single service's perspective.
"""

# Register the debugging prompt
mcp.add_prompt("debug", debug_prompt)

# Start the MCP server
if __name__ == "__main__":
    mcp.start()
