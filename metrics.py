import os
import logging
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Setup logging
logger = logging.getLogger(__name__)

# Metrics configuration
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

# Define metrics
CHECKMARKS = Counter(
    "checkmarks_total", 
    "Total number of checkmarks",
    ["chat_type"]  # private or group
)

ACTIVE_USERS = Gauge(
    "active_users", 
    "Number of active users",
    ["timeframe"]  # daily, weekly, monthly
)

STREAK_LENGTHS = Histogram(
    "streak_lengths", 
    "Distribution of streak lengths",
    ["chat_type"],  # private or group
    buckets=[1, 3, 5, 7, 14, 30, 60, 90, 180, 365]
)

COMMAND_CALLS = Counter(
    "command_calls_total", 
    "Total number of command calls",
    ["command"]
)

REMINDER_SENDS = Counter(
    "reminder_sends_total", 
    "Total number of reminders sent",
    ["type"]  # daily or missed
)

DB_OPERATION_LATENCY = Histogram(
    "db_operation_latency_seconds", 
    "Database operation latency in seconds",
    ["operation"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

CACHE_HITS = Counter(
    "cache_hits_total", 
    "Total number of cache hits",
    ["type"]
)

CACHE_MISSES = Counter(
    "cache_misses_total", 
    "Total number of cache misses",
    ["type"]
)

def setup_metrics():
    """Set up Prometheus metrics server."""
    if not METRICS_ENABLED:
        logger.info("Metrics are disabled")
        return
    
    try:
        start_http_server(METRICS_PORT)
        logger.info(f"Metrics server started on port {METRICS_PORT}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

def record_checkmark(chat_type="private"):
    """Record a checkmark."""
    if METRICS_ENABLED:
        CHECKMARKS.labels(chat_type=chat_type).inc()

def record_active_user(timeframe="daily"):
    """Record an active user."""
    if METRICS_ENABLED:
        ACTIVE_USERS.labels(timeframe=timeframe).inc()

def record_streak_length(streak, chat_type="private"):
    """Record a streak length."""
    if METRICS_ENABLED:
        STREAK_LENGTHS.labels(chat_type=chat_type).observe(streak)

def record_command_call(command):
    """Record a command call."""
    if METRICS_ENABLED:
        COMMAND_CALLS.labels(command=command).inc()

def record_reminder_send(reminder_type="daily"):
    """Record a reminder send."""
    if METRICS_ENABLED:
        REMINDER_SENDS.labels(type=reminder_type).inc()

def record_db_operation_latency(operation, seconds):
    """Record database operation latency."""
    if METRICS_ENABLED:
        DB_OPERATION_LATENCY.labels(operation=operation).observe(seconds)

def record_cache_hit(cache_type):
    """Record a cache hit."""
    if METRICS_ENABLED:
        CACHE_HITS.labels(type=cache_type).inc()

def record_cache_miss(cache_type):
    """Record a cache miss."""
    if METRICS_ENABLED:
        CACHE_MISSES.labels(type=cache_type).inc() 