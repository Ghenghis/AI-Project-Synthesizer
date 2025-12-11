"""
AI Project Synthesizer - Metrics & Timing System

Precise timing metrics for:
- Action-to-action latency (ms)
- Response times
- Workflow performance
- System health metrics
"""

import time
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
import statistics

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


@dataclass
class TimingRecord:
    """Single timing measurement."""
    action: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return self.duration_ms / 1000


@dataclass
class ActionMetrics:
    """Aggregated metrics for an action."""
    action: str
    count: int = 0
    total_ms: float = 0
    min_ms: float = float('inf')
    max_ms: float = 0
    success_count: int = 0
    failure_count: int = 0
    samples: List[float] = field(default_factory=list)

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count > 0 else 0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.count if self.count > 0 else 0

    @property
    def p50_ms(self) -> float:
        """50th percentile (median)."""
        if not self.samples:
            return 0
        return statistics.median(self.samples)

    @property
    def p95_ms(self) -> float:
        """95th percentile."""
        if len(self.samples) < 2:
            return self.max_ms
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[idx]

    @property
    def p99_ms(self) -> float:
        """99th percentile."""
        if len(self.samples) < 2:
            return self.max_ms
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[idx]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "count": self.count,
            "avg_ms": round(self.avg_ms, 2),
            "min_ms": round(self.min_ms, 2) if self.min_ms != float('inf') else 0,
            "max_ms": round(self.max_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "success_rate": round(self.success_rate * 100, 1),
        }


class ActionTimer:
    """
    Context manager for timing actions.
    
    Usage:
        async with ActionTimer("search_github") as timer:
            results = await search()
            timer.add_metadata({"results": len(results)})
    """

    def __init__(
        self,
        action: str,
        collector: Optional["MetricsCollector"] = None,
    ):
        self.action = action
        self.collector = collector or get_metrics_collector()
        self.start_time: float = 0
        self.end_time: float = 0
        self.success: bool = True
        self.metadata: Dict[str, Any] = {}

    async def __aenter__(self) -> "ActionTimer":
        self.start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.success = exc_type is None

        duration_ms = (self.end_time - self.start_time) * 1000

        record = TimingRecord(
            action=self.action,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_ms=duration_ms,
            success=self.success,
            metadata=self.metadata,
        )

        self.collector.record(record)

        # Log slow actions
        if duration_ms > 1000:
            secure_logger.warning(
                f"Slow action: {self.action} took {duration_ms:.2f}ms"
            )

    def add_metadata(self, data: Dict[str, Any]):
        """Add metadata to the timing record."""
        self.metadata.update(data)

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time so far."""
        return (time.perf_counter() - self.start_time) * 1000


class MetricsCollector:
    """
    Collects and aggregates timing metrics.
    
    Features:
    - Per-action metrics
    - Percentile calculations
    - Real-time monitoring
    - Export to various formats
    """

    def __init__(self, max_samples: int = 1000):
        self._metrics: Dict[str, ActionMetrics] = {}
        self._records: List[TimingRecord] = []
        self._max_samples = max_samples
        self._start_time = time.time()

    def record(self, record: TimingRecord):
        """Record a timing measurement."""
        self._records.append(record)

        # Keep only recent records
        if len(self._records) > self._max_samples * 10:
            self._records = self._records[-self._max_samples * 5:]

        # Update aggregated metrics
        if record.action not in self._metrics:
            self._metrics[record.action] = ActionMetrics(action=record.action)
        metrics = self._metrics[record.action]
        metrics.count += 1
        metrics.total_ms += record.duration_ms
        metrics.min_ms = min(metrics.min_ms, record.duration_ms)
        metrics.max_ms = max(metrics.max_ms, record.duration_ms)

        if record.success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1

        # Keep samples for percentile calculation
        metrics.samples.append(record.duration_ms)
        if len(metrics.samples) > self._max_samples:
            metrics.samples = metrics.samples[-self._max_samples:]

    def get_metrics(self, action: str) -> Optional[ActionMetrics]:
        """Get metrics for a specific action."""
        return self._metrics.get(action)

    def get_all_metrics(self) -> Dict[str, ActionMetrics]:
        """Get all metrics."""
        return dict(self._metrics)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "total_actions": sum(m.count for m in self._metrics.values()),
            "actions": {
                name: metrics.to_dict()
                for name, metrics in self._metrics.items()
            },
        }

    def get_recent_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent timing records."""
        return [
            {
                "action": r.action,
                "duration_ms": round(r.duration_ms, 2),
                "success": r.success,
                "metadata": r.metadata,
            }
            for r in self._records[-limit:]
        ]

    def reset(self):
        """Reset all metrics."""
        self._metrics.clear()
        self._records.clear()
        self._start_time = time.time()


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def timed(action: str):
    """
    Decorator to time async functions.
    
    Usage:
        @timed("search_github")
        async def search_github(query: str):
            ...
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            async with ActionTimer(action):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
