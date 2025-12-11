"""
AI Project Synthesizer - Observability Module

Enterprise-grade observability with correlation IDs, metrics collection,
and health checks for production monitoring.
"""

import asyncio
import time
import uuid
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class CorrelationManager:
    """
    Manages correlation IDs for request tracing across the pipeline.

    Provides context for tracking operations across multiple components
    and external API calls.
    """

    def __init__(self):
        self._local = threading.local()

    def generate_id(self) -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current context."""
        self._local.correlation_id = correlation_id

    def get_correlation_id(self) -> str:
        """Get correlation ID for current context."""
        return getattr(self._local, 'correlation_id', None)

    def clear_correlation_id(self):
        """Clear correlation ID from current context."""
        if hasattr(self._local, 'correlation_id'):
            delattr(self._local, 'correlation_id')

    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """
        Context manager for correlation ID.

        Args:
            correlation_id: Optional correlation ID, generates if None
        """
        if correlation_id is None:
            correlation_id = self.generate_id()

        old_id = self.get_correlation_id()
        self.set_correlation_id(correlation_id)

        try:
            yield correlation_id
        finally:
            if old_id:
                self.set_correlation_id(old_id)
            else:
                self.clear_correlation_id()


# Global correlation manager
correlation_manager = CorrelationManager()


@dataclass
class MetricValue:
    """Single metric value with timestamp."""
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricType:
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricsCollector:
    """
    Collects and manages application metrics.

    Supports counters, gauges, histograms, and timers with
    configurable retention and aggregation.
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum values to keep per metric
        """
        self._metrics: Dict[str, List[MetricValue]] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """
        Increment counter metric.

        Args:
            name: Metric name
            value: Increment value
            tags: Optional tags
        """
        with self._lock:
            self._counters[name] += value
            self._metrics[name].append(MetricValue(value, tags=tags or {}))

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set gauge metric value.

        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags
        """
        with self._lock:
            self._gauges[name] = value
            self._metrics[name].append(MetricValue(value, tags=tags or {}))

    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """
        Record timer metric.

        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Optional tags
        """
        with self._lock:
            self._metrics[name].append(MetricValue(duration, tags=tags or {}))

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record histogram value.

        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags
        """
        with self._lock:
            self._metrics[name].append(MetricValue(value, tags=tags or {}))

    def get_counter(self, name: str) -> float:
        """Get counter value."""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self._gauges.get(name, 0.0)

    def get_metric_values(self, name: str, since: Optional[float] = None) -> List[MetricValue]:
        """
        Get metric values.

        Args:
            name: Metric name
            since: Optional timestamp filter

        Returns:
            List of metric values
        """
        values = list(self._metrics.get(name, []))
        if since:
            values = [v for v in values if v.timestamp >= since]
        return values

    def get_metric_summary(self, name: str, since: Optional[float] = None) -> Dict[str, Any]:
        """
        Get metric summary statistics.

        Args:
            name: Metric name
            since: Optional timestamp filter

        Returns:
            Summary statistics
        """
        values = self.get_metric_values(name, since)
        if not values:
            return {}

        numeric_values = [v.value for v in values]
        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "sum": sum(numeric_values),
            "latest": numeric_values[-1] if numeric_values else None,
        }

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metrics summary."""
        result = {}

        # Counters
        for name, value in self._counters.items():
            result[f"counter:{name}"] = {"value": value, "type": "counter"}

        # Gauges
        for name, value in self._gauges.items():
            result[f"gauge:{name}"] = {"value": value, "type": "gauge"}

        # Recent metrics with summaries
        for name in self._metrics:
            summary = self.get_metric_summary(name, time.time() - 300)  # Last 5 minutes
            if summary:
                result[f"metric:{name}"] = {**summary, "type": "histogram"}

        return result

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()


# Global metrics collector
metrics = MetricsCollector()


class HealthCheck:
    """
    Individual health check implementation.
    """

    def __init__(self, name: str, check_func: Callable, timeout: float = 10.0):
        """
        Initialize health check.

        Args:
            name: Check name
            check_func: Async function that returns True if healthy
            timeout: Check timeout
        """
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.last_check = None
        self.last_status = None
        self.last_error = None

    async def check(self) -> Dict[str, Any]:
        """
        Execute health check.

        Returns:
            Health check result
        """
        start_time = time.time()

        try:
            result = await asyncio.wait_for(self.check_func(), timeout=self.timeout)
            duration = time.time() - start_time

            self.last_check = time.time()
            self.last_status = "healthy" if result else "unhealthy"
            self.last_error = None

            return {
                "name": self.name,
                "status": self.last_status,
                "duration": duration,
                "timestamp": self.last_check,
            }

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.last_check = time.time()
            self.last_status = "timeout"
            self.last_error = f"Health check timed out after {self.timeout}s"

            return {
                "name": self.name,
                "status": "timeout",
                "duration": duration,
                "timestamp": self.last_check,
                "error": self.last_error,
            }

        except Exception as e:
            duration = time.time() - start_time
            self.last_check = time.time()
            self.last_status = "error"
            self.last_error = str(e)

            return {
                "name": self.name,
                "status": "error",
                "duration": duration,
                "timestamp": self.last_check,
                "error": self.last_error,
            }


class HealthChecker:
    """
    Manages and executes multiple health checks.
    """

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._lock = threading.Lock()

    def add_check(self, check: HealthCheck):
        """Add health check."""
        with self._lock:
            self._checks[check.name] = check

    def remove_check(self, name: str):
        """Remove health check."""
        with self._lock:
            self._checks.pop(name, None)

    async def check_all(self) -> Dict[str, Any]:
        """
        Execute all health checks.

        Returns:
            Overall health status and individual check results
        """
        results = {}
        overall_status = "healthy"

        # Execute all checks concurrently
        tasks = []
        check_names = []

        with self._lock:
            for name, check in self._checks.items():
                tasks.append(check.check())
                check_names.append(name)

        if tasks:
            check_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(check_names, check_results):
                if isinstance(result, Exception):
                    results[name] = {
                        "name": name,
                        "status": "error",
                        "error": str(result),
                        "timestamp": time.time(),
                    }
                    overall_status = "unhealthy"
                else:
                    results[name] = result
                    if result["status"] != "healthy":
                        overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": results,
        }

    async def check_single(self, name: str) -> Optional[Dict[str, Any]]:
        """Execute single health check."""
        with self._lock:
            check = self._checks.get(name)

        if not check:
            return None

        return await check.check()

    def get_check_names(self) -> List[str]:
        """Get all check names."""
        with self._lock:
            return list(self._checks.keys())


# Global health checker
health_checker = HealthChecker()


# Built-in health checks
async def check_ollama_health() -> bool:
    """Check if Ollama is accessible."""
    try:
        import httpx
        settings = __import__('src.core.config', fromlist=['get_settings']).get_settings()

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.llm.ollama_host}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def check_github_api_health() -> bool:
    """Check if GitHub API is accessible."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://api.github.com/rate_limit")
            return response.status_code == 200
    except Exception:
        return False


async def check_disk_space_health() -> bool:
    """Check if sufficient disk space is available."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        # Check if at least 1GB free
        return free > 1024 * 1024 * 1024
    except Exception:
        return False


# Register built-in health checks
health_checker.add_check(HealthCheck("ollama", check_ollama_health, timeout=5.0))
health_checker.add_check(HealthCheck("github_api", check_github_api_health, timeout=5.0))
health_checker.add_check(HealthCheck("disk_space", check_disk_space_health, timeout=2.0))


class PerformanceTracker:
    """
    Tracks performance metrics for operations.
    """

    def __init__(self):
        self._operations: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def record_operation(self, operation: str, duration: float):
        """Record operation duration."""
        with self._lock:
            self._operations[operation].append(duration)
            # Keep only last 1000 measurements
            if len(self._operations[operation]) > 1000:
                self._operations[operation] = self._operations[operation][-1000:]

    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Get operation statistics."""
        with self._lock:
            durations = self._operations.get(operation, [])

        if not durations:
            return {}

        return {
            "count": len(durations),
            "avg": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations),
            "p99": sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 100 else max(durations),
        }


# Global performance tracker
performance = PerformanceTracker()


@contextmanager
def track_performance(operation: str):
    """
    Context manager for tracking operation performance.

    Args:
        operation: Operation name
    """
    start_time = time.time()
    correlation_id = correlation_manager.get_correlation_id()

    try:
        yield
    finally:
        duration = time.time() - start_time
        performance.record_operation(operation, duration)
        metrics.record_timer(f"{operation}_duration", duration,
                           tags={"correlation_id": correlation_id} if correlation_id else None)


def track_metrics(metric_type: str, name: str, tags: Optional[Dict[str, str]] = None):
    """
    Decorator for tracking function metrics.

    Args:
        metric_type: Type of metric (counter, timer, histogram)
        name: Metric name
        tags: Optional tags

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_manager.get_correlation_id()

            try:
                result = await func(*args, **kwargs)

                if metric_type == "counter":
                    metrics.increment(f"{name}_success", tags=tags)
                elif metric_type in ["timer", "histogram"]:
                    duration = time.time() - start_time
                    if metric_type == "timer":
                        metrics.record_timer(name, duration, tags=tags)
                    else:
                        metrics.record_histogram(name, duration, tags=tags)

                return result

            except Exception:
                if metric_type == "counter":
                    metrics.increment(f"{name}_error", tags=tags)
                raise

        return async_wrapper
    return decorator


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_manager.get_correlation_id()


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    correlation_manager.set_correlation_id(correlation_id)


async def check_lmstudio_health() -> Dict[str, Any]:
    """
    Health check for LM Studio service.

    Returns:
        Health check result with status and details
    """
    try:
        from src.llm.lmstudio_client import LMStudioClient

        client = LMStudioClient()
        is_healthy = await client.is_available()

        await client.close()

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "details": "LM Studio is available" if is_healthy else "LM Studio is not available",
        }
    except Exception as e:
        return {
            "status": "error",
            "details": f"LM Studio health check failed: {str(e)[:200]}",
        }


# Register default health checks
async def register_default_health_checks():
    """Register default health checks for the system."""
    from src.llm.ollama_client import OllamaClient

    # Ollama health check
    async def check_ollama():
        client = OllamaClient()
        try:
            is_healthy = await client.is_available()
            await client.close()
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "details": "Ollama is available" if is_healthy else "Ollama is not available",
            }
        except Exception as e:
            return {
                "status": "error",
                "details": f"Ollama health check failed: {str(e)[:200]}",
            }

    # LM Studio health check
    health_checker.add_check(HealthCheck("lmstudio", check_lmstudio_health, timeout=10.0))
    health_checker.add_check(HealthCheck("ollama", check_ollama, timeout=10.0))
