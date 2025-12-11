"""
AI Project Synthesizer - Telemetry System

OPT-IN usage analytics for:
- Understanding usage patterns
- Improving features
- Identifying issues

PRIVACY:
- Disabled by default
- No personal data collected
- No code/content transmitted
- Only aggregate metrics
- Can be disabled anytime
"""

import hashlib
import platform
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from src.core.version import get_version
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


@dataclass
class TelemetryEvent:
    """A telemetry event."""
    event_type: str
    timestamp: float = field(default_factory=time.time)
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event_type,
            "ts": self.timestamp,
            "props": self.properties,
        }


@dataclass
class TelemetryConfig:
    """Telemetry configuration."""
    enabled: bool = False  # OPT-IN: Disabled by default
    anonymous_id: str = ""  # Anonymous machine ID
    send_interval_seconds: int = 3600  # Send every hour
    local_storage_path: Path = Path(".cache/telemetry.json")

    # What to track
    track_searches: bool = True
    track_assemblies: bool = True
    track_errors: bool = True
    track_performance: bool = True


class TelemetryCollector:
    """
    Opt-in telemetry collector.
    
    PRIVACY FIRST:
    - Disabled by default
    - No personal data
    - No code content
    - Only aggregate metrics
    
    Usage:
        telemetry = TelemetryCollector()
        
        # Enable (opt-in)
        telemetry.enable()
        
        # Track events
        telemetry.track("search", {"platform": "github", "results": 10})
        
        # Disable anytime
        telemetry.disable()
    """

    def __init__(self, config: Optional[TelemetryConfig] = None):
        """Initialize telemetry collector."""
        self.config = config or TelemetryConfig()
        self._events: List[TelemetryEvent] = []
        self._session_start = time.time()

        # Generate anonymous ID if not set
        if not self.config.anonymous_id:
            self.config.anonymous_id = self._generate_anonymous_id()

        # Load saved config
        self._load_config()

    def _generate_anonymous_id(self) -> str:
        """Generate anonymous machine ID."""
        # Hash of machine info - no personal data
        data = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _load_config(self):
        """Load saved telemetry config."""
        config_path = Path(".cache/telemetry_config.json")
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                self.config.enabled = data.get("enabled", False)
                self.config.anonymous_id = data.get("anonymous_id", self.config.anonymous_id)
            except Exception:
                pass

    def _save_config(self):
        """Save telemetry config."""
        config_path = Path(".cache/telemetry_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "enabled": self.config.enabled,
            "anonymous_id": self.config.anonymous_id,
        }))

    def enable(self):
        """Enable telemetry (opt-in)."""
        self.config.enabled = True
        self._save_config()
        secure_logger.info("Telemetry enabled (thank you for helping improve the project!)")

    def disable(self):
        """Disable telemetry."""
        self.config.enabled = False
        self._events.clear()
        self._save_config()
        secure_logger.info("Telemetry disabled")

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self.config.enabled

    def track(self, event_type: str, properties: Dict[str, Any] = None):
        """
        Track an event.
        
        Only tracks if telemetry is enabled.
        No personal data is included.
        """
        if not self.config.enabled:
            return

        # Sanitize properties - remove any potential PII
        safe_props = self._sanitize_properties(properties or {})

        event = TelemetryEvent(
            event_type=event_type,
            properties=safe_props,
        )

        self._events.append(event)

        # Save locally
        self._save_events()

    def _sanitize_properties(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any potential PII from properties."""
        safe = {}

        # Allowed keys (whitelist approach)
        allowed_keys = {
            "platform", "platforms", "count", "results", "duration_ms",
            "success", "error_type", "version", "python_version",
            "os", "resource_type", "cache_hit",
        }

        for key, value in props.items():
            if key in allowed_keys:
                # Only include simple values
                if isinstance(value, (str, int, float, bool)):
                    safe[key] = value
                elif isinstance(value, list) and all(isinstance(v, str) for v in value):
                    safe[key] = value

        return safe

    def _save_events(self):
        """Save events locally."""
        try:
            self.config.local_storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "anonymous_id": self.config.anonymous_id,
                "version": get_version(),
                "events": [e.to_dict() for e in self._events[-100:]],  # Keep last 100
            }

            self.config.local_storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            secure_logger.debug(f"Failed to save telemetry: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get local telemetry stats."""
        return {
            "enabled": self.config.enabled,
            "events_count": len(self._events),
            "session_duration_seconds": time.time() - self._session_start,
            "anonymous_id": self.config.anonymous_id[:8] + "...",
        }

    # Convenience methods for common events
    def track_search(self, platforms: List[str], results_count: int, duration_ms: float):
        """Track a search event."""
        if self.config.track_searches:
            self.track("search", {
                "platforms": platforms,
                "count": results_count,
                "duration_ms": duration_ms,
            })

    def track_assembly(self, success: bool, resources_count: int, duration_ms: float):
        """Track a project assembly."""
        if self.config.track_assemblies:
            self.track("assembly", {
                "success": success,
                "count": resources_count,
                "duration_ms": duration_ms,
            })

    def track_error(self, error_type: str):
        """Track an error (type only, no details)."""
        if self.config.track_errors:
            self.track("error", {
                "error_type": error_type,
            })


# Global telemetry instance
_telemetry: Optional[TelemetryCollector] = None


def get_telemetry() -> TelemetryCollector:
    """Get or create telemetry collector."""
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryCollector()
    return _telemetry


def track(event_type: str, properties: Dict[str, Any] = None):
    """Quick function to track an event."""
    get_telemetry().track(event_type, properties)
