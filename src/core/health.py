"""
AI Project Synthesizer - Health Checks & Monitoring

Professional health check system for:
- Service status monitoring
- Dependency verification
- API connectivity checks
- Resource availability
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.core.security import get_secure_logger
from src.core.version import get_version

secure_logger = get_secure_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component."""

    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0.0
    last_check: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": c.latency_ms,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


class HealthChecker:
    """
    System health checker.

    Monitors all components and provides health status.
    """

    def __init__(self):
        """Initialize health checker."""
        self._start_time = time.time()
        self._last_check: SystemHealth | None = None

    async def check_all(self) -> SystemHealth:
        """Run all health checks."""
        components = []

        # Check each component
        components.append(await self._check_lm_studio())
        components.append(await self._check_ollama())
        components.append(await self._check_github())
        components.append(await self._check_huggingface())
        components.append(await self._check_kaggle())
        components.append(await self._check_elevenlabs())
        components.append(await self._check_openai())

        # Determine overall status
        statuses = [c.status for c in components]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.DEGRADED

        health = SystemHealth(
            status=overall,
            version=get_version(),
            uptime_seconds=time.time() - self._start_time,
            components=components,
        )

        self._last_check = health
        return health

    async def _check_lm_studio(self) -> ComponentHealth:
        """Check LM Studio connectivity."""
        start = time.time()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get("http://localhost:1234/v1/models")

                if response.status_code == 200:
                    models = response.json().get("data", [])
                    return ComponentHealth(
                        name="lm_studio",
                        status=HealthStatus.HEALTHY,
                        message=f"{len(models)} models loaded",
                        latency_ms=(time.time() - start) * 1000,
                        details={"models": [m.get("id") for m in models[:3]]},
                    )
        except Exception:
            pass

        return ComponentHealth(
            name="lm_studio",
            status=HealthStatus.UNHEALTHY,
            message="Not running or unreachable",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_ollama(self) -> ComponentHealth:
        """Check Ollama connectivity."""
        start = time.time()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get("http://localhost:11434/api/tags")

                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return ComponentHealth(
                        name="ollama",
                        status=HealthStatus.HEALTHY,
                        message=f"{len(models)} models available",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except Exception:
            pass

        return ComponentHealth(
            name="ollama",
            status=HealthStatus.UNKNOWN,
            message="Not running (optional)",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_github(self) -> ComponentHealth:
        """Check GitHub API connectivity."""
        start = time.time()
        try:
            from src.core.config import get_settings

            settings = get_settings()
            token = settings.platforms.github_token.get_secret_value()

            if not token:
                return ComponentHealth(
                    name="github",
                    status=HealthStatus.UNHEALTHY,
                    message="No token configured",
                )

            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"},
                )

                if response.status_code == 200:
                    user = response.json()
                    return ComponentHealth(
                        name="github",
                        status=HealthStatus.HEALTHY,
                        message=f"Authenticated as {user.get('login')}",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except Exception:
            pass

        return ComponentHealth(
            name="github",
            status=HealthStatus.DEGRADED,
            message="API check failed",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_huggingface(self) -> ComponentHealth:
        """Check HuggingFace API."""
        start = time.time()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("https://huggingface.co/api/models?limit=1")

                if response.status_code == 200:
                    return ComponentHealth(
                        name="huggingface",
                        status=HealthStatus.HEALTHY,
                        message="API accessible",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except Exception:
            pass

        return ComponentHealth(
            name="huggingface",
            status=HealthStatus.DEGRADED,
            message="API unreachable",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_kaggle(self) -> ComponentHealth:
        """Check Kaggle API."""
        start = time.time()
        try:
            from src.core.config import get_settings

            settings = get_settings()

            if settings.platforms.kaggle_username and settings.platforms.kaggle_key:
                return ComponentHealth(
                    name="kaggle",
                    status=HealthStatus.HEALTHY,
                    message="Credentials configured",
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception:
            pass

        return ComponentHealth(
            name="kaggle",
            status=HealthStatus.UNKNOWN,
            message="Not configured",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_elevenlabs(self) -> ComponentHealth:
        """Check ElevenLabs API."""
        start = time.time()
        try:
            from src.core.config import get_settings

            settings = get_settings()
            api_key = settings.elevenlabs.elevenlabs_api_key.get_secret_value()

            if not api_key:
                return ComponentHealth(
                    name="elevenlabs",
                    status=HealthStatus.UNKNOWN,
                    message="Not configured",
                )

            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.elevenlabs.io/v1/user", headers={"xi-api-key": api_key}
                )

                if response.status_code == 200:
                    return ComponentHealth(
                        name="elevenlabs",
                        status=HealthStatus.HEALTHY,
                        message="API accessible",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except Exception:
            pass

        return ComponentHealth(
            name="elevenlabs",
            status=HealthStatus.DEGRADED,
            message="API check failed",
            latency_ms=(time.time() - start) * 1000,
        )

    async def _check_openai(self) -> ComponentHealth:
        """Check OpenAI API."""
        start = time.time()
        try:
            from src.core.config import get_settings

            settings = get_settings()
            api_key = settings.llm.openai_api_key.get_secret_value()

            if not api_key:
                return ComponentHealth(
                    name="openai",
                    status=HealthStatus.UNKNOWN,
                    message="Not configured",
                )

            return ComponentHealth(
                name="openai",
                status=HealthStatus.HEALTHY,
                message="Configured",
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception:
            pass

        return ComponentHealth(
            name="openai",
            status=HealthStatus.UNKNOWN,
            message="Not configured",
            latency_ms=(time.time() - start) * 1000,
        )


# Global health checker
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get or create health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


async def check_health() -> SystemHealth:
    """Quick function to check system health."""
    checker = get_health_checker()
    return await checker.check_all()
