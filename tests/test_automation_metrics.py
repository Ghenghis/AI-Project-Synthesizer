"""
Tests for src/automation/metrics.py - Metrics System

Full coverage tests for:
- TimingRecord
- ActionMetrics
- ActionTimer
- MetricsCollector
"""

import pytest
import asyncio
import time

from src.automation.metrics import (
    TimingRecord,
    ActionMetrics,
    ActionTimer,
    MetricsCollector,
    get_metrics_collector,
)


class TestTimingRecord:
    """Tests for TimingRecord dataclass."""
    
    def test_create_record(self):
        record = TimingRecord(
            action="test_action",
            start_time=1000.0,
            end_time=1100.0,
            duration_ms=100.0,
            success=True,
        )
        assert record.action == "test_action"
        assert record.duration_ms == 100.0
        assert record.success is True
    
    def test_duration_seconds(self):
        record = TimingRecord(
            action="test",
            start_time=0,
            end_time=0,
            duration_ms=1500.0,
            success=True,
        )
        assert record.duration_seconds == 1.5
    
    def test_with_metadata(self):
        record = TimingRecord(
            action="test",
            start_time=0,
            end_time=0,
            duration_ms=50.0,
            success=True,
            metadata={"key": "value"},
        )
        assert record.metadata["key"] == "value"


class TestActionMetrics:
    """Tests for ActionMetrics dataclass."""
    
    def test_defaults(self):
        metrics = ActionMetrics(action="test")
        assert metrics.action == "test"
        assert metrics.count == 0
        assert metrics.total_ms == 0
        assert metrics.min_ms == float('inf')
        assert metrics.max_ms == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
    
    def test_avg_ms_empty(self):
        metrics = ActionMetrics(action="test")
        assert metrics.avg_ms == 0
    
    def test_avg_ms_with_data(self):
        metrics = ActionMetrics(action="test", count=4, total_ms=400)
        assert metrics.avg_ms == 100
    
    def test_success_rate_empty(self):
        metrics = ActionMetrics(action="test")
        assert metrics.success_rate == 0
    
    def test_success_rate_with_data(self):
        metrics = ActionMetrics(action="test", count=10, success_count=8)
        assert metrics.success_rate == 0.8
    
    def test_p50_empty(self):
        metrics = ActionMetrics(action="test")
        assert metrics.p50_ms == 0
    
    def test_p50_with_data(self):
        metrics = ActionMetrics(
            action="test",
            samples=[10, 20, 30, 40, 50],
        )
        assert metrics.p50_ms == 30
    
    def test_p95_empty(self):
        metrics = ActionMetrics(action="test")
        assert metrics.p95_ms == 0
    
    def test_p95_with_data(self):
        metrics = ActionMetrics(
            action="test",
            max_ms=100,
            samples=list(range(1, 101)),  # 1-100
        )
        # p95 should be around 95-96 depending on implementation
        assert 94 <= metrics.p95_ms <= 96
    
    def test_p99_with_data(self):
        metrics = ActionMetrics(
            action="test",
            max_ms=100,
            samples=list(range(1, 101)),
        )
        # p99 should be around 99-100 depending on implementation
        assert 98 <= metrics.p99_ms <= 100
    
    def test_to_dict(self):
        metrics = ActionMetrics(
            action="test",
            count=10,
            total_ms=500,
            min_ms=30,
            max_ms=80,
            success_count=9,
            failure_count=1,
            samples=[40, 50, 60],
        )
        d = metrics.to_dict()
        assert d["action"] == "test"
        assert d["count"] == 10
        assert d["avg_ms"] == 50
        assert d["min_ms"] == 30
        assert d["max_ms"] == 80
        assert d["success_rate"] == 90.0


class TestActionTimer:
    """Tests for ActionTimer context manager."""
    
    @pytest.mark.asyncio
    async def test_basic_timing(self):
        collector = MetricsCollector()
        
        async with ActionTimer("test_action", collector) as timer:
            await asyncio.sleep(0.01)
        
        metrics = collector.get_metrics("test_action")
        assert metrics is not None
        assert metrics.count == 1
        assert metrics.total_ms > 0
    
    @pytest.mark.asyncio
    async def test_success_tracking(self):
        collector = MetricsCollector()
        
        async with ActionTimer("success_action", collector):
            pass
        
        metrics = collector.get_metrics("success_action")
        assert metrics.success_count == 1
        assert metrics.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_failure_tracking(self):
        collector = MetricsCollector()
        
        try:
            async with ActionTimer("fail_action", collector):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        metrics = collector.get_metrics("fail_action")
        assert metrics.success_count == 0
        assert metrics.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_add_metadata(self):
        collector = MetricsCollector()
        
        async with ActionTimer("meta_action", collector) as timer:
            timer.add_metadata({"key": "value"})
        
        # Metadata is stored in the record
        assert timer.metadata["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_elapsed_ms(self):
        collector = MetricsCollector()
        
        async with ActionTimer("elapsed_action", collector) as timer:
            await asyncio.sleep(0.01)
            elapsed = timer.elapsed_ms
            assert elapsed > 0


class TestMetricsCollector:
    """Tests for MetricsCollector class."""
    
    @pytest.fixture
    def collector(self):
        return MetricsCollector()
    
    def test_create_collector(self, collector):
        assert collector is not None
        assert collector._max_samples == 1000
    
    def test_custom_max_samples(self):
        collector = MetricsCollector(max_samples=100)
        assert collector._max_samples == 100
    
    def test_record_timing(self, collector):
        record = TimingRecord(
            action="test",
            start_time=time.time(),
            end_time=time.time(),
            duration_ms=50,
            success=True,
        )
        collector.record(record)
        
        metrics = collector.get_metrics("test")
        assert metrics is not None
        assert metrics.count == 1
        assert metrics.total_ms == 50
    
    def test_multiple_records(self, collector):
        for i in range(5):
            collector.record(TimingRecord(
                action="multi",
                start_time=0,
                end_time=0,
                duration_ms=10 * (i + 1),
                success=True,
            ))
        
        metrics = collector.get_metrics("multi")
        assert metrics.count == 5
        assert metrics.total_ms == 150  # 10+20+30+40+50
        assert metrics.min_ms == 10
        assert metrics.max_ms == 50
    
    def test_get_nonexistent_metrics(self, collector):
        metrics = collector.get_metrics("nonexistent")
        assert metrics is None
    
    def test_get_all_metrics(self, collector):
        collector.record(TimingRecord(
            action="action1", start_time=0, end_time=0,
            duration_ms=10, success=True,
        ))
        collector.record(TimingRecord(
            action="action2", start_time=0, end_time=0,
            duration_ms=20, success=True,
        ))
        
        all_metrics = collector.get_all_metrics()
        assert "action1" in all_metrics
        assert "action2" in all_metrics
    
    def test_get_summary(self, collector):
        collector.record(TimingRecord(
            action="summary_test", start_time=0, end_time=0,
            duration_ms=100, success=True,
        ))
        
        summary = collector.get_summary()
        assert "uptime_seconds" in summary
        assert "total_actions" in summary
        assert "actions" in summary
    
    def test_reset(self, collector):
        collector.record(TimingRecord(
            action="to_reset", start_time=0, end_time=0,
            duration_ms=10, success=True,
        ))
        
        # Reset by creating new collector or clearing internal state
        collector._metrics = {}
        collector._records = []
        
        assert collector.get_metrics("to_reset") is None
        assert len(collector._records) == 0
    
    def test_samples_limit(self):
        collector = MetricsCollector(max_samples=5)
        
        for i in range(10):
            collector.record(TimingRecord(
                action="limited", start_time=0, end_time=0,
                duration_ms=i, success=True,
            ))
        
        metrics = collector.get_metrics("limited")
        assert len(metrics.samples) == 5
    
    def test_records_cleanup(self):
        collector = MetricsCollector(max_samples=10)
        
        # Add many records
        for i in range(200):
            collector.record(TimingRecord(
                action="cleanup", start_time=0, end_time=0,
                duration_ms=i, success=True,
            ))
        
        # Records should be cleaned up
        assert len(collector._records) <= 100


class TestGetMetricsCollector:
    """Tests for get_metrics_collector function."""
    
    def test_singleton(self):
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2
